"""Telephony provider wrapper (Twilio) with a mock fallback.

Design goals:
  - The rest of the app calls ``send_sms`` / ``validate_signature`` and never
    imports the Twilio SDK directly.
  - The Twilio SDK is imported lazily, so the engine runs (and tests pass) with
    no telephony package installed when ``use_mock_sms`` is on.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.config import Settings, get_settings


@dataclass
class SmsResult:
    sid: str | None
    status: str  # sent | mock_sent | failed
    price: float | None = None
    error: str | None = None


class TelephonyClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _is_mock(self) -> bool:
        return self.settings.use_mock_sms or not self.settings.twilio_configured

    def send_sms(self, *, to: str, from_: str, body: str) -> SmsResult:
        """Send an SMS. In mock mode, records a fake success instead of calling out."""
        if self._is_mock:
            return SmsResult(sid=f"MOCK-{uuid.uuid4().hex[:16]}", status="mock_sent")

        try:
            # Lazy import — only needed for real sends.
            from twilio.rest import Client

            client = Client(
                self.settings.twilio_account_sid, self.settings.twilio_auth_token
            )
            msg = client.messages.create(to=to, from_=from_, body=body)
            price = float(msg.price) if getattr(msg, "price", None) else None
            return SmsResult(sid=msg.sid, status=msg.status or "sent", price=price)
        except Exception as exc:  # noqa: BLE001 — surface any provider error to the log
            return SmsResult(sid=None, status="failed", error=str(exc))

    def validate_signature(self, *, url: str, params: dict, signature: str | None) -> bool:
        """Validate an inbound Twilio webhook signature.

        Returns True when validation is disabled or in mock mode so local testing
        isn't blocked. In production set CALLCATCH_VALIDATE_TWILIO_SIGNATURE=true.
        """
        if not self.settings.validate_twilio_signature:
            return True
        if not self.settings.twilio_configured or not signature:
            return False
        try:
            from twilio.request_validator import RequestValidator

            validator = RequestValidator(self.settings.twilio_auth_token)
            return validator.validate(url, params, signature)
        except Exception:  # noqa: BLE001
            return False


def get_client() -> TelephonyClient:
    return TelephonyClient()
