"""
template_optimizer.py — Autonomous A/B test engine and template rewriter.

How it works:
  1. Runs on a schedule (e.g., weekly) against all active templates
  2. Identifies templates with enough sends (≥ min threshold) but below reply rate floor
  3. Fetches the top 3 performing templates for the same step/persona as context
  4. Asks Claude to generate a challenger variant, explaining what to fix
  5. Retires the underperformer, saves the challenger

This is the "self-improving" part of the agent — it closes the feedback loop
between send performance and template generation.
"""

import json
import re
import anthropic

from config import cfg
from modules.database.crud import (
    get_underperforming_templates, get_active_template,
    retire_template, save_template
)
from modules.database.models import SessionLocal, TemplateVariant
from modules.psychology.frameworks import FRAMEWORKS

_claude = anthropic.Anthropic(api_key=cfg.anthropic_api_key)


def _summarize_template(t: TemplateVariant) -> str:
    return (
        f"Step {t.sequence_step} | {t.industry} | {t.persona_type} | "
        f"Framework: {t.psych_framework} | "
        f"Sends: {t.sends} | Replies: {t.replies} | "
        f"Reply rate: {t.reply_rate:.1%} | Positive rate: {t.positive_rate:.1%}\n"
        f"Subject: {t.subject_template}\n"
        f"Body: {t.body_template[:300]}..."
    )


def _generate_challenger(
    underperformer: TemplateVariant,
    top_performers: list[TemplateVariant],
) -> tuple[str, str] | None:
    """
    Asks Claude to write a challenger variant given the underperformer's copy
    and examples of what IS working.

    Returns (subject_template, body_template) or None on failure.
    """
    framework = FRAMEWORKS.get(underperformer.psych_framework)
    framework_directives = (
        "\n".join(f"  - {d}" for d in framework.email_directives)
        if framework else "Use strong, direct copywriting."
    )

    top_examples = "\n\n".join(
        f"PERFORMER {i+1} (reply rate {t.reply_rate:.1%}):\n{_summarize_template(t)}"
        for i, t in enumerate(top_performers)
    ) if top_performers else "No top performers yet — write fresh."

    prompt = f"""You are a cold email optimization specialist.

UNDERPERFORMING TEMPLATE (reply rate {underperformer.reply_rate:.1%} — needs improvement):
{_summarize_template(underperformer)}

TOP PERFORMING TEMPLATES FOR REFERENCE:
{top_examples}

BEHAVIORAL FRAMEWORK IN USE: {underperformer.psych_framework}
FRAMEWORK DIRECTIVES:
{framework_directives}

Your job: Write a challenger variant that will outperform the underperformer.
Analyze what makes the top performers work. Apply those patterns.
Keep the same sequence step purpose but change the angle, hook, and phrasing.

Use {{first_name}} and {{company}} as template variables.

Return JSON only:
{{"subject": "the subject template", "body": "the full body template"}}"""

    response = _claude.messages.create(
        model=cfg.claude_model,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
        return parsed.get("subject", ""), parsed.get("body", "")
    except Exception as e:
        print(f"[Optimizer] Failed to parse challenger: {e}")
        return None


def run_optimization_pass() -> dict:
    """
    Main optimization runner. Finds underperformers, generates challengers, swaps them in.
    Returns a summary of what was replaced.
    """
    db = SessionLocal()
    replaced = 0
    skipped = 0

    try:
        underperformers = get_underperforming_templates(db, cfg.reply_rate_floor)

        for template in underperformers:
            if template.reply_rate >= cfg.reply_rate_floor:
                skipped += 1
                continue

            # Find what IS working for this same step/persona combo
            top_performers = (
                db.query(TemplateVariant)
                .filter(
                    TemplateVariant.sequence_step == template.sequence_step,
                    TemplateVariant.persona_type == template.persona_type,
                    TemplateVariant.is_active == True,
                    TemplateVariant.sends >= 5,
                )
                .order_by(TemplateVariant.reply_rate.desc())
                .limit(3)
                .all()
            )

            result = _generate_challenger(template, top_performers)
            if not result:
                skipped += 1
                continue

            new_subject, new_body = result
            if not new_subject or not new_body:
                skipped += 1
                continue

            # Retire the underperformer
            retire_template(db, template.id)

            # Save the challenger
            save_template(
                db=db,
                sequence_step=template.sequence_step,
                industry=template.industry,
                persona_type=template.persona_type,
                psych_framework=template.psych_framework,
                subject_template=new_subject,
                body_template=new_body,
                is_active=True,
                is_control=False,
            )

            replaced += 1
            print(
                f"[Optimizer] Replaced template {template.id} "
                f"(step {template.sequence_step}, {template.industry}, "
                f"reply_rate={template.reply_rate:.1%})"
            )

    finally:
        db.close()

    summary = {"replaced": replaced, "skipped": skipped}
    print(f"[Optimizer] Pass complete: {summary}")
    return summary
