"""SQLAlchemy ORM models for the Call Catch engine.

Four tables:
  - BusinessProfile : a tenant (the business whose calls we catch)
  - MessageTemplate : the auto-text copy, one active template per type per business
  - CallLog         : every inbound call attempt we're told about
  - SmsLog          : every outbound auto-text, with delivery status
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # The business's telephony number that callers dial (E.164, e.g. +14045551234).
    # This is how we route an inbound webhook to the right tenant.
    twilio_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # Where the SMS is sent *from* (defaults to the twilio_number if unset).
    sms_from_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    owner_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    templates: Mapped[list["MessageTemplate"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    call_logs: Mapped[list["CallLog"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
    sms_logs: Mapped[list["SmsLog"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )

    @property
    def from_number(self) -> str:
        return self.sms_from_number or self.twilio_number


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True
    )

    name: Mapped[str] = mapped_column(String(120), default="Default")
    # "default" | "business_hours" | "after_hours"
    template_type: Mapped[str] = mapped_column(String(32), default="default", index=True)

    # Body supports {business} and {caller} placeholders.
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    business: Mapped["BusinessProfile"] = relationship(back_populates="templates")


class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int | None] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Provider call identifier (Twilio CallSid / Telnyx call_control_id).
    provider_call_sid: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="twilio")

    from_number: Mapped[str] = mapped_column(String(32), index=True)  # the caller
    to_number: Mapped[str] = mapped_column(String(32), index=True)    # the business
    direction: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Raw provider status: completed | no-answer | busy | failed | ...
    status: Mapped[str] = mapped_column(String(32), index=True)
    # Our interpretation: did we treat this as a missed call?
    is_missed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    # Did we kick off an auto-text for this call?
    auto_text_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    call_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    business: Mapped["BusinessProfile | None"] = relationship(back_populates="call_logs")
    sms_logs: Mapped[list["SmsLog"]] = relationship(back_populates="call_log")


class SmsLog(Base):
    __tablename__ = "sms_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE"), index=True
    )
    call_log_id: Mapped[int | None] = mapped_column(
        ForeignKey("call_logs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True
    )

    to_number: Mapped[str] = mapped_column(String(32), index=True)   # the caller
    from_number: Mapped[str] = mapped_column(String(32))             # the business
    body: Mapped[str] = mapped_column(Text, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), default="twilio")
    provider_message_sid: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # queued | sending | sent | delivered | failed | mock_sent
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)

    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )

    business: Mapped["BusinessProfile"] = relationship(back_populates="sms_logs")
    call_log: Mapped["CallLog | None"] = relationship(back_populates="sms_logs")
