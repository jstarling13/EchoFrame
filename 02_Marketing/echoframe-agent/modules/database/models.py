"""
models.py — SQLAlchemy ORM models for leads, outreach sequences, and analytics.

SQLite for local/dev, swap DATABASE_URL for PostgreSQL in production.
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Enum, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import cfg

Base = declarative_base()
engine = create_engine(cfg.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


class LeadStage(PyEnum):
    NEW = "new"
    QUALIFIED = "qualified"
    IN_SEQUENCE = "in_sequence"
    REPLIED = "replied"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    QUESTION = "question"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    UNSUBSCRIBED = "unsubscribed"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Identity
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(30))
    title = Column(String(100))
    linkedin_url = Column(String(300))

    # Company
    company_name = Column(String(200))
    industry = Column(String(100))
    website = Column(String(300))
    city = Column(String(100))
    state = Column(String(50))
    employee_count = Column(Integer)
    estimated_revenue = Column(Float)

    # Scoring
    lead_score = Column(Float, default=0.0)   # 0–100
    persona_type = Column(String(50))          # e.g. "risk_averse_smb_owner"
    has_verified_email = Column(Boolean, default=False)
    has_phone = Column(Boolean, default=False)

    # Pipeline
    stage = Column(Enum(LeadStage), default=LeadStage.NEW)
    source = Column(String(50))               # "apollo", "google_cse", "manual"
    disqualified_reason = Column(String(200))

    # Relationships
    touches = relationship("OutreachTouch", back_populates="lead")
    replies = relationship("Reply", back_populates="lead")


class OutreachTouch(Base):
    __tablename__ = "outreach_touches"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)

    sequence_step = Column(Integer)            # 1–5
    subject_line = Column(String(300))
    body_text = Column(Text)
    template_variant = Column(String(50))      # for A/B tracking
    psych_framework = Column(String(100))      # which framework was applied

    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    resend_message_id = Column(String(100))    # Resend API message ID for tracking

    lead = relationship("Lead", back_populates="touches")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)

    raw_body = Column(Text)
    intent = Column(String(30))           # "positive", "negative", "question", "auto_reply"
    intent_confidence = Column(Float)     # 0–1
    intent_reasoning = Column(Text)       # LLM's chain-of-thought

    responded_at = Column(DateTime)       # when agent sent follow-up
    response_body = Column(Text)

    lead = relationship("Lead", back_populates="replies")


class TemplateVariant(Base):
    __tablename__ = "template_variants"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    retired_at = Column(DateTime)

    sequence_step = Column(Integer)
    industry = Column(String(100))
    persona_type = Column(String(50))
    psych_framework = Column(String(100))

    subject_template = Column(Text)
    body_template = Column(Text)

    sends = Column(Integer, default=0)
    opens = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    positive_replies = Column(Integer, default=0)

    is_control = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    @property
    def reply_rate(self) -> float:
        return self.replies / self.sends if self.sends > 0 else 0.0

    @property
    def positive_rate(self) -> float:
        return self.positive_replies / self.sends if self.sends > 0 else 0.0


def init_db():
    Base.metadata.create_all(engine)
