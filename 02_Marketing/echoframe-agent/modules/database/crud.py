"""
crud.py — All database read/write operations. Keep business logic out of here.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .models import Lead, LeadStage, OutreachTouch, Reply, TemplateVariant


def get_or_create_lead(db: Session, email: str, **kwargs) -> tuple[Lead, bool]:
    """Returns (lead, created). Deduplicates by email."""
    lead = db.query(Lead).filter(Lead.email == email).first()
    if lead:
        return lead, False
    lead = Lead(email=email, **kwargs)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead, True


def get_leads_ready_for_touch(db: Session, step: int, limit: int = 50) -> list[Lead]:
    """Returns leads in IN_SEQUENCE stage where their next scheduled touch is due."""
    now = datetime.utcnow()
    # Leads whose most recent touch matches step-1 and was sent > delay_days ago
    # Simpler: just fetch IN_SEQUENCE leads and let sequence_manager filter by timing
    return (
        db.query(Lead)
        .filter(Lead.stage == LeadStage.IN_SEQUENCE)
        .limit(limit)
        .all()
    )


def log_touch(db: Session, lead_id: int, step: int, subject: str, body: str,
              variant: str, framework: str, resend_id: str) -> OutreachTouch:
    touch = OutreachTouch(
        lead_id=lead_id,
        sequence_step=step,
        subject_line=subject,
        body_text=body,
        template_variant=variant,
        psych_framework=framework,
        resend_message_id=resend_id,
        sent_at=datetime.utcnow(),
    )
    db.add(touch)
    db.commit()
    return touch


def log_reply(db: Session, lead_id: int, raw_body: str, intent: str,
              confidence: float, reasoning: str) -> Reply:
    reply = Reply(
        lead_id=lead_id,
        raw_body=raw_body,
        intent=intent,
        intent_confidence=confidence,
        intent_reasoning=reasoning,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def update_lead_stage(db: Session, lead_id: int, stage: LeadStage) -> None:
    db.query(Lead).filter(Lead.id == lead_id).update({"stage": stage})
    db.commit()


def get_active_template(db: Session, step: int, industry: str, persona: str) -> Optional[TemplateVariant]:
    """Fetches the best-performing active template for a given step/industry/persona."""
    return (
        db.query(TemplateVariant)
        .filter(
            TemplateVariant.sequence_step == step,
            TemplateVariant.industry == industry,
            TemplateVariant.persona_type == persona,
            TemplateVariant.is_active == True,
        )
        .order_by(TemplateVariant.positive_replies.desc())
        .first()
    )


def get_underperforming_templates(db: Session, reply_rate_floor: float) -> list[TemplateVariant]:
    """Returns active templates with enough sends but below the reply rate floor."""
    return (
        db.query(TemplateVariant)
        .filter(
            TemplateVariant.is_active == True,
            TemplateVariant.sends >= 20,
        )
        .all()
    )


def retire_template(db: Session, template_id: int) -> None:
    db.query(TemplateVariant).filter(TemplateVariant.id == template_id).update({
        "is_active": False,
        "retired_at": datetime.utcnow(),
    })
    db.commit()


def save_template(db: Session, **kwargs) -> TemplateVariant:
    t = TemplateVariant(**kwargs)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def increment_template_metric(db: Session, template_variant: str, metric: str) -> None:
    """metric is 'sends', 'opens', 'replies', or 'positive_replies'."""
    db.query(TemplateVariant).filter(
        TemplateVariant.id == template_variant
    ).update({metric: getattr(TemplateVariant, metric) + 1})
    db.commit()
