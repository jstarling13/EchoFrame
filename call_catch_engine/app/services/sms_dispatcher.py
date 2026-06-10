"""Automated SMS dispatcher.

``dispatch_missed_call_sms`` is the background task triggered when a missed call
is logged. It:
  1. waits a short, configurable delay so the text feels natural,
  2. opens its *own* DB session (the request session is long gone by now),
  3. picks the active MessageTemplate for the business (business-hours aware),
  4. renders + sends the SMS via the telephony client,
  5. records an SmsLog row with the final delivery status.

It is defensive on purpose: a missed text should never crash the worker.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import BusinessProfile, CallLog, MessageTemplate, SmsLog
from app.services.twilio_client import get_client

logger = logging.getLogger("call_catch.dispatcher")


def _is_after_hours(tz_name: str, now: datetime | None = None) -> bool:
    """Default coverage window: Mon–Fri, 08:00–17:00 local. Outside that = after hours."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:  # noqa: BLE001 — unknown tz falls back to UTC
        tz = timezone.utc
    local = (now or datetime.now(timezone.utc)).astimezone(tz)
    if local.weekday() >= 5:  # Sat/Sun
        return True
    return local.hour < 8 or local.hour >= 17


def select_template(
    db, business: BusinessProfile, now: datetime | None = None
) -> MessageTemplate | None:
    """Pick the best active template: time-appropriate type, then default, then any."""
    desired = "after_hours" if _is_after_hours(business.timezone, now) else "business_hours"
    order = [desired, "default"]

    for ttype in order:
        tmpl = db.scalar(
            select(MessageTemplate).where(
                MessageTemplate.business_id == business.id,
                MessageTemplate.template_type == ttype,
                MessageTemplate.is_active.is_(True),
            )
        )
        if tmpl:
            return tmpl

    # Last resort: any active template.
    return db.scalar(
        select(MessageTemplate).where(
            MessageTemplate.business_id == business.id,
            MessageTemplate.is_active.is_(True),
        )
    )


def render_template(body: str, *, business_name: str, caller_number: str) -> str:
    """Token replacement that tolerates stray braces in the copy."""
    return body.replace("{business}", business_name).replace("{caller}", caller_number)


async def dispatch_missed_call_sms(
    call_log_id: int, delay_seconds: int | None = None
) -> None:
    settings = get_settings()
    delay = settings.sms_send_delay_seconds if delay_seconds is None else delay_seconds

    scheduled_for = datetime.now(timezone.utc) + timedelta(seconds=max(delay, 0))
    if delay > 0:
        await asyncio.sleep(delay)

    db = SessionLocal()
    try:
        call = db.get(CallLog, call_log_id)
        if call is None or call.business_id is None:
            logger.warning("dispatch: call %s missing or unlinked; skipping", call_log_id)
            return

        business = db.get(BusinessProfile, call.business_id)
        if business is None or not business.is_active:
            logger.info("dispatch: business inactive/missing for call %s", call_log_id)
            return

        template = select_template(db, business)
        if template is None:
            logger.warning("dispatch: no active template for business %s", business.id)
            return

        body = render_template(
            template.body,
            business_name=business.name,
            caller_number=call.from_number,
        )

        # Record the attempt up front so we never "lose" a send.
        sms = SmsLog(
            business_id=business.id,
            call_log_id=call.id,
            template_id=template.id,
            to_number=call.from_number,
            from_number=business.from_number,
            body=body,
            status="sending",
            scheduled_for=scheduled_for,
        )
        db.add(sms)
        db.commit()
        db.refresh(sms)

        result = get_client().send_sms(
            to=call.from_number, from_=business.from_number, body=body
        )

        sms.provider_message_sid = result.sid
        sms.status = result.status
        sms.price = result.price
        sms.error_message = result.error
        if result.status in {"sent", "mock_sent", "delivered", "queued"}:
            sms.sent_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            "dispatch: call %s -> sms %s status=%s", call_log_id, sms.id, sms.status
        )
    except Exception:  # noqa: BLE001 — background task must not bubble up
        logger.exception("dispatch: unexpected error for call %s", call_log_id)
        db.rollback()
    finally:
        db.close()
