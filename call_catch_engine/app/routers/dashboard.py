"""Dashboard + admin REST endpoints.

Read endpoints power the "Missed Call Log Dashboard" UI; the write endpoints
exist so you can provision a business + templates without a separate admin tool.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BusinessProfile, CallLog, MessageTemplate, SmsLog
from app.schemas import (
    BusinessCreate,
    BusinessOut,
    CallLogOut,
    DashboardSummary,
    SmsLogOut,
    TemplateCreate,
    TemplateOut,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


def _get_business_or_404(db: Session, business_id: int) -> BusinessProfile:
    business = db.get(BusinessProfile, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


# ── Provisioning ────────────────────────────────────────────────────────────
@router.post("/businesses", response_model=BusinessOut, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)) -> BusinessProfile:
    existing = db.scalar(
        select(BusinessProfile).where(
            BusinessProfile.twilio_number == payload.twilio_number
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="twilio_number already registered")
    business = BusinessProfile(**payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/businesses", response_model=list[BusinessOut])
def list_businesses(db: Session = Depends(get_db)) -> list[BusinessProfile]:
    return list(db.scalars(select(BusinessProfile).order_by(BusinessProfile.id)))


@router.get("/businesses/{business_id}", response_model=BusinessOut)
def get_business(business_id: int, db: Session = Depends(get_db)) -> BusinessProfile:
    return _get_business_or_404(db, business_id)


@router.post(
    "/businesses/{business_id}/templates", response_model=TemplateOut, status_code=201
)
def create_template(
    business_id: int, payload: TemplateCreate, db: Session = Depends(get_db)
) -> MessageTemplate:
    _get_business_or_404(db, business_id)
    tmpl = MessageTemplate(business_id=business_id, **payload.model_dump())
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.get("/businesses/{business_id}/templates", response_model=list[TemplateOut])
def list_templates(business_id: int, db: Session = Depends(get_db)) -> list[MessageTemplate]:
    _get_business_or_404(db, business_id)
    return list(
        db.scalars(
            select(MessageTemplate)
            .where(MessageTemplate.business_id == business_id)
            .order_by(MessageTemplate.id)
        )
    )


# ── Dashboard reads ─────────────────────────────────────────────────────────
@router.get("/businesses/{business_id}/calls", response_model=list[CallLogOut])
def list_calls(
    business_id: int,
    missed_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CallLog]:
    _get_business_or_404(db, business_id)
    stmt = select(CallLog).where(CallLog.business_id == business_id)
    if missed_only:
        stmt = stmt.where(CallLog.is_missed.is_(True))
    stmt = stmt.order_by(CallLog.occurred_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/businesses/{business_id}/sms", response_model=list[SmsLogOut])
def list_sms(
    business_id: int,
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[SmsLog]:
    _get_business_or_404(db, business_id)
    stmt = select(SmsLog).where(SmsLog.business_id == business_id)
    if status:
        stmt = stmt.where(SmsLog.status == status.lower())
    stmt = stmt.order_by(SmsLog.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt))


@router.get("/businesses/{business_id}/dashboard", response_model=DashboardSummary)
def dashboard_summary(business_id: int, db: Session = Depends(get_db)) -> DashboardSummary:
    _get_business_or_404(db, business_id)

    def _count(stmt) -> int:
        return db.scalar(stmt) or 0

    total_calls = _count(
        select(func.count(CallLog.id)).where(CallLog.business_id == business_id)
    )
    missed_calls = _count(
        select(func.count(CallLog.id)).where(
            CallLog.business_id == business_id, CallLog.is_missed.is_(True)
        )
    )
    texts_sent = _count(
        select(func.count(SmsLog.id)).where(
            SmsLog.business_id == business_id,
            SmsLog.status.in_(["sent", "mock_sent", "delivered", "queued"]),
        )
    )
    texts_delivered = _count(
        select(func.count(SmsLog.id)).where(
            SmsLog.business_id == business_id, SmsLog.status == "delivered"
        )
    )
    texts_failed = _count(
        select(func.count(SmsLog.id)).where(
            SmsLog.business_id == business_id, SmsLog.status == "failed"
        )
    )

    recent_missed = list(
        db.scalars(
            select(CallLog)
            .where(CallLog.business_id == business_id, CallLog.is_missed.is_(True))
            .order_by(CallLog.occurred_at.desc())
            .limit(10)
        )
    )
    recent_texts = list(
        db.scalars(
            select(SmsLog)
            .where(SmsLog.business_id == business_id)
            .order_by(SmsLog.created_at.desc())
            .limit(10)
        )
    )

    recovery_rate = round(texts_sent / missed_calls, 3) if missed_calls else 0.0

    return DashboardSummary(
        business_id=business_id,
        total_calls=total_calls,
        missed_calls=missed_calls,
        texts_sent=texts_sent,
        texts_delivered=texts_delivered,
        texts_failed=texts_failed,
        recovery_rate=recovery_rate,
        recent_missed_calls=[CallLogOut.model_validate(c) for c in recent_missed],
        recent_texts=[SmsLogOut.model_validate(s) for s in recent_texts],
    )
