"""Seed a demo business + templates so you can exercise the engine immediately.

    cd call_catch_engine
    python seed.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal, init_db
from app.models import BusinessProfile, MessageTemplate

DEMO_NUMBER = "+14045550100"

BUSINESS_HOURS_BODY = (
    "Hi! This is {business}. Sorry we missed your call — we're with another "
    "customer and will call you right back. Or reply here and we'll help you now."
)
AFTER_HOURS_BODY = (
    "Hi! This is {business}. Thanks for calling — we're closed right now but got "
    "your missed call. Reply with what you need and we'll get back to you first thing."
)


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        business = db.scalar(
            select(BusinessProfile).where(BusinessProfile.twilio_number == DEMO_NUMBER)
        )
        if business is None:
            business = BusinessProfile(
                name="Reliable Heating & Air",
                twilio_number=DEMO_NUMBER,
                owner_phone="+14045550111",
                timezone="America/New_York",
            )
            db.add(business)
            db.commit()
            db.refresh(business)

            db.add_all(
                [
                    MessageTemplate(
                        business_id=business.id,
                        name="Business hours",
                        template_type="business_hours",
                        body=BUSINESS_HOURS_BODY,
                    ),
                    MessageTemplate(
                        business_id=business.id,
                        name="After hours",
                        template_type="after_hours",
                        body=AFTER_HOURS_BODY,
                    ),
                ]
            )
            db.commit()
            print(f"Seeded business #{business.id} ({business.name}) at {DEMO_NUMBER}")
        else:
            print(f"Demo business already exists: #{business.id} ({business.name})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
