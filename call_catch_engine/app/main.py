"""Call Catch engine — FastAPI application entrypoint.

Run locally:
    cd call_catch_engine
    uvicorn app.main:app --reload --port 8020
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.database import init_db
from app.routers import dashboard, webhooks

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(
    title="EchoFrame · Call Catch Engine",
    version=__version__,
    description="Listens for missed-call webhooks and auto-texts the caller within ~60s.",
)

app.include_router(webhooks.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def _on_startup() -> None:
    # Dev convenience: ensure tables exist. In production, run Alembic migrations
    # instead and remove this call.
    init_db()


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "call-catch-engine",
        "version": __version__,
        "mock_sms": settings.use_mock_sms or not settings.twilio_configured,
        "delay_seconds": settings.sms_send_delay_seconds,
    }
