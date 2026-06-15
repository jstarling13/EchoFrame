"""Environment-driven settings for the Call Catch engine.

All settings are read from environment variables (or a local .env file) prefixed
with ``CALLCATCH_``. See ``.env.example`` for the full list.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CALLCATCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite:///./call_catch.db"

    # Dispatch behaviour
    sms_send_delay_seconds: int = 45

    # Telephony / Twilio
    use_mock_sms: bool = True
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    validate_twilio_signature: bool = False
    public_base_url: str = "http://localhost:8000"

    # Which inbound call statuses should trigger an auto-text.
    missed_statuses: list[str] = Field(
        default_factory=lambda: ["no-answer", "busy", "failed"]
    )

    @field_validator("missed_statuses", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow MISSED_STATUSES to be provided as a comma-separated string."""
        if isinstance(value, str):
            return [v.strip().lower() for v in value.split(",") if v.strip()]
        return value

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token)


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so settings are parsed once per process."""
    return Settings()
