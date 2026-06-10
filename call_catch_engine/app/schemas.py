"""Pydantic schemas: webhook inputs, create payloads, and dashboard responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Webhook input ───────────────────────────────────────────────────────────
class TwilioVoiceWebhook(BaseModel):
    """Subset of Twilio's voice status-callback form fields we care about.

    Twilio posts application/x-www-form-urlencoded; we also accept the analogous
    Telnyx fields via aliases handled in the router.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    call_sid: str | None = Field(default=None, alias="CallSid")
    from_number: str = Field(alias="From")
    to_number: str = Field(alias="To")
    call_status: str = Field(alias="CallStatus")
    direction: str | None = Field(default=None, alias="Direction")
    call_duration: int | None = Field(default=None, alias="CallDuration")


# ── Create payloads (admin/testing) ─────────────────────────────────────────
class BusinessCreate(BaseModel):
    name: str
    twilio_number: str
    sms_from_number: str | None = None
    owner_phone: str | None = None
    timezone: str = "America/New_York"


class TemplateCreate(BaseModel):
    name: str = "Default"
    template_type: str = "default"
    body: str
    is_active: bool = True


# ── Responses ───────────────────────────────────────────────────────────────
class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    twilio_number: str
    sms_from_number: str | None
    owner_phone: str | None
    timezone: str
    is_active: bool
    created_at: datetime


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    name: str
    template_type: str
    body: str
    is_active: bool
    created_at: datetime


class CallLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int | None
    provider_call_sid: str | None
    provider: str
    from_number: str
    to_number: str
    direction: str | None
    status: str
    is_missed: bool
    auto_text_triggered: bool
    call_duration_seconds: int | None
    occurred_at: datetime
    created_at: datetime


class SmsLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    call_log_id: int | None
    to_number: str
    from_number: str
    body: str
    provider: str
    provider_message_sid: str | None
    status: str
    error_message: str | None
    scheduled_for: datetime | None
    sent_at: datetime | None
    created_at: datetime


class WebhookAck(BaseModel):
    received: bool = True
    call_log_id: int | None = None
    is_missed: bool = False
    auto_text_scheduled: bool = False


class DashboardSummary(BaseModel):
    business_id: int
    total_calls: int
    missed_calls: int
    texts_sent: int
    texts_delivered: int
    texts_failed: int
    recovery_rate: float  # missed calls that got a text, as a fraction
    recent_missed_calls: list[CallLogOut]
    recent_texts: list[SmsLogOut]
