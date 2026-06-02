"""
sequence_manager.py — Orchestrates the 5-touch outreach sequence for each lead.

Responsibilities:
  - Determine which leads need their next touch today
  - Generate the email via the copywriter
  - Enforce send windows (Tue–Thu, 7–9am)
  - Send via Resend
  - Log to DB
  - Halt sequence when a reply is received
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import cfg
from modules.database.crud import (
    get_leads_ready_for_touch, log_touch, update_lead_stage,
    get_active_template, save_template
)
from modules.database.models import Lead, LeadStage, OutreachTouch, SessionLocal
from modules.outreach.email_sender import send_email
from modules.psychology.copywriter import generate_email, GeneratedEmail


def _is_within_send_window() -> bool:
    """Returns True if current time is within the configured send window."""
    now = datetime.now()
    # cfg.send_days: Mon=0, Tue=1, Wed=2, Thu=3
    if now.weekday() not in cfg.send_days:
        return False
    if not (cfg.send_hour_start <= now.hour < cfg.send_hour_end):
        return False
    return True


def _days_since_last_touch(lead: Lead) -> int | None:
    """Returns the number of days since the lead's last outreach touch, or None if never contacted."""
    if not lead.touches:
        return None
    last = max(lead.touches, key=lambda t: t.sent_at or datetime.min)
    if not last.sent_at:
        return None
    return (datetime.utcnow() - last.sent_at).days


def _next_sequence_step(lead: Lead) -> int | None:
    """
    Returns the next sequence step number for this lead (1–5), or None if sequence is complete.
    """
    completed_steps = sorted(
        [t.sequence_step for t in lead.touches if t.sent_at is not None]
    )
    if not completed_steps:
        return 1
    last_step = completed_steps[-1]
    if last_step >= 5:
        return None  # Sequence complete
    return last_step + 1


def _is_due_for_next_touch(lead: Lead) -> bool:
    """
    Returns True if the lead is due for their next touch based on sequence timing.
    Uses cfg.sequence_delays_days to determine the gap between steps.
    """
    next_step = _next_sequence_step(lead)
    if next_step is None:
        return False
    if next_step == 1:
        return True  # First touch — always due if we're in the send window

    days_since = _days_since_last_touch(lead)
    if days_since is None:
        return True

    # sequence_delays_days[0] = 0 (send immediately), [1] = 3 days, etc.
    required_gap = cfg.sequence_delays_days[next_step - 1]
    return days_since >= required_gap


def process_sequence_for_lead(lead: Lead, db: Session, dry_run: bool = False) -> bool:
    """
    Processes the next sequence step for a single lead.
    Returns True if an email was sent, False otherwise.

    dry_run=True: generates the email but does not send or log it.
    """
    if not _is_due_for_next_touch(lead):
        return False

    next_step = _next_sequence_step(lead)
    if next_step is None:
        update_lead_stage(db, lead.id, LeadStage.CLOSED_LOST)
        return False

    # Check if there's a saved high-performing template to use
    saved_template = get_active_template(db, next_step, lead.industry or "", lead.persona_type or "")

    if saved_template:
        # Use the saved template with variable substitution
        subject = saved_template.subject_template.replace("{first_name}", lead.first_name or "there")
        subject = subject.replace("{company}", lead.company_name or "your business")
        body = saved_template.body_template.replace("{first_name}", lead.first_name or "there")
        body = body.replace("{company}", lead.company_name or "your business")
        framework_name = saved_template.psych_framework
        variant_id = str(saved_template.id)
    else:
        # Generate fresh via Claude
        try:
            email: GeneratedEmail = generate_email(
                first_name=lead.first_name or "there",
                company_name=lead.company_name or "your business",
                industry=lead.industry or "small business",
                city=lead.city or "Columbus",
                employee_count=lead.employee_count or 5,
                persona_type=lead.persona_type or "risk_averse_smb_owner",
                sequence_step=next_step,
            )
        except Exception as e:
            print(f"[Sequence] Email generation failed for lead {lead.id}: {e}")
            return False

        subject = email.subject
        body = email.body
        framework_name = email.framework_used
        variant_id = f"generated_{next_step}_{email.framework_used}"

        # Persist this as a new template variant so it can be A/B tested
        save_template(
            db=db,
            sequence_step=next_step,
            industry=lead.industry or "",
            persona_type=lead.persona_type or "",
            psych_framework=framework_name,
            subject_template=subject.replace(lead.first_name or "there", "{first_name}"),
            body_template=body.replace(lead.first_name or "there", "{first_name}"),
            is_active=True,
        )

    if dry_run:
        print(f"\n[DRY RUN] Lead: {lead.email} | Step {next_step}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}\n")
        return True

    # Send
    message_id = send_email(
        to_email=lead.email,
        to_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or lead.email,
        subject=subject,
        body_text=body,
    )

    if not message_id:
        return False

    # Log the touch
    log_touch(
        db=db,
        lead_id=lead.id,
        step=next_step,
        subject=subject,
        body=body,
        variant=variant_id,
        framework=framework_name,
        resend_id=message_id,
    )

    # Update stage
    if lead.stage == LeadStage.QUALIFIED:
        update_lead_stage(db, lead.id, LeadStage.IN_SEQUENCE)

    return True


def run_sequence_batch(limit: int = 50, dry_run: bool = False, force_send_window: bool = False) -> dict:
    """
    Main batch runner. Processes up to `limit` leads due for a sequence touch.

    force_send_window=True bypasses the time-of-day check (useful for testing).
    Returns summary dict with counts.
    """
    if not force_send_window and not _is_within_send_window():
        print(f"[Sequence] Outside send window — skipping. (Tue–Thu, 7–9am)")
        return {"sent": 0, "skipped": 0, "errors": 0, "reason": "outside_send_window"}

    db = SessionLocal()
    sent = skipped = errors = 0

    try:
        leads = get_leads_ready_for_touch(db, step=1, limit=limit)
        for lead in leads:
            if lead.stage in (LeadStage.REPLIED, LeadStage.POSITIVE, LeadStage.NEGATIVE,
                              LeadStage.UNSUBSCRIBED, LeadStage.CLOSED_WON, LeadStage.CLOSED_LOST):
                skipped += 1
                continue
            try:
                result = process_sequence_for_lead(lead, db, dry_run=dry_run)
                if result:
                    sent += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"[Sequence] Error on lead {lead.id}: {e}")
                errors += 1
    finally:
        db.close()

    summary = {"sent": sent, "skipped": skipped, "errors": errors}
    print(f"[Sequence] Batch complete: {summary}")
    return summary
