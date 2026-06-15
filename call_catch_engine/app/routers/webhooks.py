"""Inbound telephony webhook router.

Receives call status callbacks, identifies missed calls, logs them, and (when
missed) schedules the delayed auto-text via FastAPI BackgroundTasks.

Two entry points:
  - POST /webhooks/twilio/voice-status   (Twilio, form-urlencoded)
  - POST /webhooks/telnyx/call-events     (Telnyx, JSON)
Both funnel into one handler so logging + dispatch logic lives in a single place.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import BusinessProfile, CallLog
from app.schemas import WebhookAck
from app.services.sms_dispatcher import dispatch_missed_call_sms
from app.services.twilio_client import get_client

logger = logging.getLogger("call_catch.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _normalize(status: str | None) -> str:
    return (status or "").strip().lower()


def _handle_call(
    *,
    db: Session,
    background_tasks: BackgroundTasks,
    provider: str,
    call_sid: str | None,
    from_number: str,
    to_number: str,
    status: str,
    direction: str | None,
    duration: int | None,
) -> WebhookAck:
    settings = get_settings()
    status_norm = _normalize(status)
    is_missed = status_norm in settings.missed_statuses

    # Route to the tenant by the dialed (business) number.
    business = db.scalar(
        select(BusinessProfile).where(BusinessProfile.twilio_number == to_number)
    )

    # Idempotency: providers retry callbacks. If we've already logged this exact
    # call+status, treat it as a duplicate delivery -- don't double-log or re-text.
    if call_sid:
        existing = db.scalar(
            select(CallLog).where(
                CallLog.provider_call_sid == call_sid,
                CallLog.status == status_norm,
            )
        )
        if existing is not None:
            logger.info(
                "duplicate webhook for call %s (%s); ignoring", call_sid, status_norm
            )
            return WebhookAck(
                received=True,
                call_log_id=existing.id,
                is_missed=existing.is_missed,
                auto_text_scheduled=False,
            )

    call = CallLog(
        business_id=business.id if business else None,
        provider=provider,
        provider_call_sid=call_sid,
        from_number=from_number,
        to_number=to_number,
        direction=direction,
        status=status_norm,
        is_missed=is_missed,
        call_duration_seconds=duration,
    )

    should_text = bool(
        is_missed and business is not None and business.is_active and from_number
    )
    call.auto_text_triggered = should_text
    db.add(call)
    db.commit()
    db.refresh(call)

    if should_text:
        # Delay handled inside the task (settings.sms_send_delay_seconds).
        background_tasks.add_task(dispatch_missed_call_sms, call.id, None)
        logger.info("missed call %s logged; auto-text scheduled", call.id)

    return WebhookAck(
        received=True,
        call_log_id=call.id,
        is_missed=is_missed,
        auto_text_scheduled=should_text,
    )


@router.post("/twilio/voice-status", response_model=WebhookAck)
async def twilio_voice_status(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_twilio_signature: str | None = Header(default=None),
) -> WebhookAck:
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}

    # Optional signature validation (no-op unless enabled in settings).
    settings = get_settings()
    url = f"{settings.public_base_url.rstrip('/')}{request.url.path}"
    if not get_client().validate_signature(
        url=url, params=params, signature=x_twilio_signature
    ):
        logger.warning("rejected Twilio webhook: bad signature")
        return WebhookAck(received=False)

    duration_raw = params.get("CallDuration")
    return _handle_call(
        db=db,
        background_tasks=background_tasks,
        provider="twilio",
        call_sid=params.get("CallSid"),
        from_number=params.get("From", ""),
        to_number=params.get("To", ""),
        status=params.get("CallStatus", ""),
        direction=params.get("Direction"),
        duration=int(duration_raw) if duration_raw and duration_raw.isdigit() else None,
    )


# Map Telnyx hangup causes to the Twilio-style vocabulary our settings use.
_TELNYX_CAUSE_MAP = {
    "no_answer": "no-answer",
    "timeout": "no-answer",
    "user_busy": "busy",
    "busy": "busy",
    "call_rejected": "failed",
    "rejected": "failed",
    "normal_clearing": "completed",
    "answered": "completed",
}


@router.post("/telnyx/call-events", response_model=WebhookAck)
async def telnyx_call_events(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> WebhookAck:
    body = await request.json()
    data = (body or {}).get("data", {})
    event_type = data.get("event_type", "")
    payload = data.get("payload", {})

    # We only act on terminal call events.
    if event_type not in {"call.hangup", "call.no_answer"}:
        return WebhookAck(received=True)

    cause = _normalize(payload.get("hangup_cause") or payload.get("hangup_source"))
    status = _TELNYX_CAUSE_MAP.get(
        cause, "no-answer" if event_type == "call.no_answer" else cause
    )

    return _handle_call(
        db=db,
        background_tasks=background_tasks,
        provider="telnyx",
        call_sid=payload.get("call_control_id") or payload.get("call_session_id"),
        from_number=payload.get("from", ""),
        to_number=payload.get("to", ""),
        status=status,
        direction=payload.get("direction"),
        duration=None,
    )
