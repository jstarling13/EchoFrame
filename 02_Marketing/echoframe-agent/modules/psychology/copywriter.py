"""
copywriter.py — The psychological copywriting engine.

This is the core intelligence of the marketing agent. It:
  1. Retrieves relevant EchoFrame KB passages for the target industry
  2. Selects the right behavioral psychology framework for the persona
  3. Constructs a structured prompt that forces the LLM to write persuasively
  4. Validates the output against quality and brand voice rules
  5. Returns a subject line + email body ready to send

The LLM (Claude) is used ONLY for prose generation. All the strategic
decisions (which framework, which pain points, which CTA) are made by
deterministic Python code above it.
"""

import json
import re
from dataclasses import dataclass

import anthropic

from config import cfg
from modules.ingestion.knowledge_base import get_value_prop_for_industry, query_kb
from modules.psychology.frameworks import PsychFramework, get_framework_for_sequence_step

client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)


@dataclass
class GeneratedEmail:
    subject: str
    body: str
    framework_used: str
    persona_type: str
    sequence_step: int


# ─── Industry-specific pain point library ────────────────────────────────────
# These are injected alongside KB context so the LLM has concrete specifics.

INDUSTRY_PAIN_POINTS = {
    "hvac": {
        "primary_leak": "miscellaneous expense bucket — typically $200–400/month of uncategorized charges",
        "benchmark_stat": "HVAC labor cost benchmarks run 28–34% of revenue; most owners I review are running 36–41%",
        "emotional_fear": "a slow season that reveals how thin the margins actually are",
        "cta_hook": "a sample report for a Columbus HVAC company exactly your size",
        "industry_work": "the HVAC business to spend your evenings staring at spreadsheets",
        "expertise": "keeping folks comfortable",
        "pain_area": "their cash flow",
        "curiosity_question": "frustrated trying to translate standard accounting reports into actual, plain-English steps for your business",
        "role_split": "You handle the HVAC work",
    },
    "plumbing": {
        "primary_leak": "material waste and truck inventory — typically 3–5% of revenue sitting idle",
        "benchmark_stat": "plumbing materials cost should run 18–25% of revenue; overstock eats cash flow",
        "emotional_fear": "losing a big commercial contract and not having 3 months of runway",
        "cta_hook": "a sample audit that shows where plumbing companies your size are bleeding",
        "industry_work": "the plumbing business to spend your evenings decoding profit-and-loss statements",
        "expertise": "solving problems other people can't fix",
        "pain_area": "where their money went",
        "curiosity_question": "frustrated trying to figure out why a busy month still doesn't feel like a profitable one",
        "role_split": "You handle the plumbing work",
    },
    "restaurant": {
        "primary_leak": "food cost percentage creep — operators rarely catch it until it's 3–4 points over target",
        "benchmark_stat": "food cost should run 28–35% of revenue; every 1% over is ~$400/month on a $40k/month restaurant",
        "emotional_fear": "a slow week that tips the P&L negative without warning",
        "cta_hook": "a food cost analysis for a Columbus restaurant with your revenue profile",
        "industry_work": "the restaurant business to spend your nights reconciling food costs against a spreadsheet",
        "expertise": "creating an experience people come back for",
        "pain_area": "their margins",
        "curiosity_question": "frustrated that the numbers at the end of the month don't seem to match how busy it felt",
        "role_split": "You run the restaurant",
    },
    "salon": {
        "primary_leak": "product inventory and retail shrinkage — often 8–12% of product revenue",
        "benchmark_stat": "salon payroll should run 45–50% of service revenue; most salons I review are at 54–60%",
        "emotional_fear": "losing a key stylist and not knowing the financial impact until month-end",
        "cta_hook": "a sample report for a Columbus salon in your revenue range",
        "industry_work": "a salon to spend your evenings buried in payroll reports and expense breakdowns",
        "expertise": "building a space people trust",
        "pain_area": "their cash flow",
        "curiosity_question": "frustrated trying to figure out where the revenue went after a strong week on the floor",
        "role_split": "You run the salon",
    },
    "electrical": {
        "primary_leak": "job costing gaps — materials quoted at one number, actual cost lands higher, difference comes out of margin",
        "benchmark_stat": "electrical contractors your size should run gross margin at 38–48%; shops below that are absorbing unbillable travel and material overruns",
        "emotional_fear": "finishing a large job, invoicing it out, and realizing weeks later the cash position barely moved",
        "cta_hook": "a sample job profitability breakdown built for a small electrical shop in your area",
        "industry_work": "an electrical business to spend your evenings trying to figure out why a job that billed well still didn't seem to pay well",
        "expertise": "the work itself",
        "pain_area": "their job costs",
        "curiosity_question": "frustrated that it's hard to tell which jobs actually made money until weeks after the invoice goes out",
        "role_split": "You handle the electrical work",
    },
    "roofing": {
        "primary_leak": "subcontractor markup mismanagement — markup set once, never updated for material inflation",
        "benchmark_stat": "roofing gross margin should run 35–45%; material cost inflation since 2022 has crushed this",
        "emotional_fear": "a slow season with no cash reserves to bridge the gap",
        "cta_hook": "a margin analysis for a Columbus roofing company in your revenue range",
        "industry_work": "the roofing business to spend your evenings figuring out which jobs actually made money",
        "expertise": "getting the job done right the first time",
        "pain_area": "their margins",
        "curiosity_question": "frustrated that material costs keep climbing but it's hard to see exactly where it hits your bottom line",
        "role_split": "You handle the roofing work",
    },
    "landscaping": {
        "primary_leak": "equipment depreciation and fuel — typically underestimated by 20–30% of actual cost",
        "benchmark_stat": "landscaping labor runs 40–55% of revenue; seasonal spikes hide the true annual figure",
        "emotional_fear": "a slow season with no recurring contracts to anchor revenue",
        "cta_hook": "a seasonal cash flow analysis for a landscaping company your size",
        "industry_work": "a landscaping business to spend your evenings trying to make sense of seasonal cash flow",
        "expertise": "making properties look their best",
        "pain_area": "their cash flow between seasons",
        "curiosity_question": "frustrated that it's hard to know what the slow season is going to look like until you're already in it",
        "role_split": "You handle the landscaping work",
    },
}

GENERIC_PAIN = {
    "primary_leak": "miscellaneous and overhead expenses that aren't tracked at the line-item level",
    "benchmark_stat": "most small businesses run 15–25% above their industry's optimal expense ratios",
    "emotional_fear": "a slow month revealing that the margin was never as good as it looked",
    "cta_hook": "a sample financial report for a business in your industry",
    "industry_work": "their business to spend evenings trying to decode their own financials",
    "expertise": "running their business",
    "pain_area": "their cash flow",
    "curiosity_question": "frustrated trying to translate what their numbers actually mean into something actionable",
    "role_split": "You run the business",
}


def _get_industry_pain(industry: str) -> dict:
    i = (industry or "").lower()
    for key in INDUSTRY_PAIN_POINTS:
        if key in i:
            return INDUSTRY_PAIN_POINTS[key]
    return GENERIC_PAIN


# ─── Sequence Step Context ────────────────────────────────────────────────────

SEQUENCE_STEP_CONTEXT = {
    1: {
        "goal": "Hook — establish a specific, concrete problem they recognize",
        "cta": "offer to send a free sample report (no call, no demo, lowest friction)",
        "length": "4–6 sentences max",
        "tone": "direct, specific, no fluff",
    },
    2: {
        "goal": "Deepen the problem — add industry benchmark data as authority signal",
        "cta": "offer the sample report again, slightly more direct",
        "length": "5–7 sentences",
        "tone": "credible, numbers-driven, slightly more urgent",
    },
    3: {
        "goal": "Social proof — show what a peer/similar business discovered",
        "cta": "propose a 15-minute call OR the sample report (their choice)",
        "length": "6–8 sentences",
        "tone": "peer-to-peer, conversational, confident",
    },
    4: {
        "goal": "Direct ask — remove all ambiguity about what you're offering and why now",
        "cta": "specific ask: 'Reply yes and I'll send you the sample report today'",
        "length": "4–5 sentences",
        "tone": "direct, respectful, no desperation",
    },
    5: {
        "goal": "Breakup — acknowledge you've reached out, give them a graceful exit, leave door open",
        "cta": "no CTA — just a door left open",
        "length": "3–4 sentences",
        "tone": "human, zero pressure, genuine",
    },
}


# ─── Prompt Assembly ──────────────────────────────────────────────────────────

STEP1_SYSTEM_PROMPT = """You are filling in a cold email template for Jacob Starling at EchoFrame.
Your only job is to slot the provided field values into the template cleanly.
Do NOT rewrite, shorten, or restructure the template. Do NOT add or remove sentences.
Make only the minimal grammar adjustments needed for the filled-in values to read naturally.
Return valid JSON only: {"subject": "...", "body": "..."}"""


def _build_system_prompt(framework: PsychFramework) -> str:
    directives = "\n".join(f"  - {d}" for d in framework.email_directives)
    forbidden = ", ".join(framework.forbidden_patterns)

    return f"""You are a cold email copywriter for EchoFrame, a financial intelligence service for small businesses.

Your writing must be:
- Conversational and human. You are writing from Jacob Starling, a local Columbus GA finance professional.
- Specific. Every claim should reference an industry, a number, or a location.
- Short. Mobile-readable. No paragraph longer than 3 sentences.
- Empathetic — lead with understanding the owner's world, not fear about their losses.

BEHAVIORAL FRAMEWORK: {framework.name.upper().replace("_", " ")}
{framework.trigger_condition}

DIRECTIVES YOU MUST FOLLOW:
{directives}

FORBIDDEN WORDS/PHRASES (if you use any of these, the email fails):
{forbidden}

OUTPUT FORMAT: Return valid JSON only, no markdown, no explanation.
{{"subject": "the subject line", "body": "the full email body"}}"""


def _build_step1_prompt(
    lead_first_name: str,
    company_name: str,
    industry: str,
    city: str,
) -> str:
    """
    Step 1 uses Jacob's exact proven template. The LLM's only job is to
    slot in the industry-specific fields cleanly — no creative rewriting.
    """
    pain = _get_industry_pain(industry)

    return f"""Fill in this cold email template for the lead below.
Follow the structure EXACTLY. Do not add sentences, remove sentences, or change the fixed lines.
Only adapt the bracketed placeholders to fit the lead.

LEAD:
  First name: {lead_first_name}
  Company: {company_name}
  Industry: {industry}
  City: {city}

TEMPLATE TO FILL IN:
Subject: A simpler way to view [Company Name]'s numbers

Hi [First Name],

You didn't get into [industry_work]. You're an expert at [expertise], but a lot of the local owners I talk to feel like they're expected to be a part-time CFO just to understand [pain_area].

Do you ever find yourself [curiosity_question]?

It shouldn't be a guessing game. I built EchoFrame specifically for non-accountant business owners here in [City]. We take a simple export of your expenses and turn it into a polished, easy-to-read Word document that checks your margins against industry benchmarks and gives you one clear action item for the month.

[role_split]; we make the numbers make sense. Would you be open to me sending over a sample report so you can see exactly what I mean? No call or demo required.

Best,
Jacob Starling
EchoFrame | Financial Intelligence for Small Business

FIELD VALUES TO USE (slot these in exactly, minor grammar adjustments only):
  [Company Name] → {company_name}
  [First Name] → {lead_first_name}
  [industry_work] → {pain.get('industry_work', 'their industry to decode their own financials')}
  [expertise] → {pain.get('expertise', 'running their business')}
  [pain_area] → {pain.get('pain_area', 'their cash flow')}
  [curiosity_question] → {pain.get('curiosity_question', 'frustrated trying to make sense of your numbers')}
  [City] → {city}
  [role_split] → {pain.get('role_split', 'You run the business')}

Return JSON only: {{"subject": "...", "body": "..."}}"""


def _build_user_prompt(
    lead_first_name: str,
    company_name: str,
    industry: str,
    city: str,
    employee_count: int,
    sequence_step: int,
    framework: PsychFramework,
    kb_passages: list[str],
) -> str:
    # Step 1 always uses Jacob's proven template — bypass the framework prompt
    if sequence_step == 1:
        return _build_step1_prompt(lead_first_name, company_name, industry, city)

    pain = _get_industry_pain(industry)
    step_ctx = SEQUENCE_STEP_CONTEXT.get(sequence_step, SEQUENCE_STEP_CONTEXT[2])
    kb_context = "\n".join(f"- {p}" for p in kb_passages[:4]) if kb_passages else ""
    example_subjects = "\n".join(f"  - {s}" for s in framework.example_subject_patterns[:2])
    example_openings = "\n".join(f"  - {o}" for o in framework.example_opening_patterns[:1])

    return f"""Write a follow-up cold email (sequence step {sequence_step} of 5) for this lead.
They did not reply to the first email. Do not reference that they haven't replied — just continue the conversation.

LEAD DETAILS:
  First name: {lead_first_name}
  Company: {company_name}
  Industry: {industry}
  City: {city}
  Employees: {employee_count}

SEQUENCE STEP GOAL: {step_ctx['goal']}
CTA FOR THIS STEP: {step_ctx['cta']}
LENGTH: {step_ctx['length']}
TONE: {step_ctx['tone']}

INDUSTRY CONTEXT:
  Primary leak: {pain['primary_leak']}
  Benchmark stat: {pain['benchmark_stat']}
  Their fear: {pain['emotional_fear']}

ECHOFRAME KNOWLEDGE BASE:
{kb_context}

SUBJECT LINE PATTERNS:
{example_subjects}

OPENING PATTERNS:
{example_openings}

SIGNATURE:
Jacob Starling
EchoFrame | Financial Intelligence for Small Business

Return JSON only: {{"subject": "...", "body": "..."}}"""


# ─── Main Generation Function ─────────────────────────────────────────────────

def generate_email(
    first_name: str,
    company_name: str,
    industry: str,
    city: str,
    employee_count: int,
    persona_type: str,
    sequence_step: int,
) -> GeneratedEmail:
    """
    Generates a psychologically-targeted cold email for a specific lead and sequence step.
    Raises ValueError if the LLM output fails quality validation.
    """
    framework = get_framework_for_sequence_step(persona_type, sequence_step)
    kb_passages = get_value_prop_for_industry(industry)

    # Step 1 uses Jacob's fixed template — minimal system prompt so LLM doesn't rewrite it
    system_prompt = STEP1_SYSTEM_PROMPT if sequence_step == 1 else _build_system_prompt(framework)
    user_prompt = _build_user_prompt(
        lead_first_name=first_name,
        company_name=company_name,
        industry=industry,
        city=city,
        employee_count=employee_count,
        sequence_step=sequence_step,
        framework=framework,
        kb_passages=kb_passages,
    )

    response = client.messages.create(
        model=cfg.claude_model,
        max_tokens=800,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if Claude adds them despite instructions
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned non-JSON output: {raw_text[:200]}") from e

    subject = parsed.get("subject", "").strip()
    body = parsed.get("body", "").strip()

    _validate_email(subject, body, framework)

    return GeneratedEmail(
        subject=subject,
        body=body,
        framework_used=framework.name,
        persona_type=persona_type,
        sequence_step=sequence_step,
    )


def _validate_email(subject: str, body: str, framework: PsychFramework) -> None:
    """Hard validation — raises ValueError if the email fails brand voice rules."""
    errors = []

    if not subject:
        errors.append("Subject line is empty.")
    if len(subject) > 80:
        errors.append(f"Subject too long ({len(subject)} chars). Max 80.")

    if not body:
        errors.append("Body is empty.")

    # Check for forbidden patterns
    combined = (subject + " " + body).lower()
    for forbidden in framework.forbidden_patterns:
        if forbidden.lower() in combined:
            errors.append(f"Forbidden pattern found: '{forbidden}'")

    # Sanity check: EchoFrame must be mentioned
    if "echoframe" not in combined:
        errors.append("Email doesn't mention EchoFrame.")

    if errors:
        raise ValueError(f"Email validation failed: {'; '.join(errors)}")


def generate_reply_response(
    original_email_body: str,
    reply_body: str,
    intent: str,
    first_name: str,
    industry: str,
) -> str:
    """
    Generates a response to a classified reply.
    Only called for 'positive' and 'question' intents.
    'negative' replies get no response.
    """
    if intent == "positive":
        instruction = (
            "The prospect replied positively. They're interested. "
            "Write a short 3–4 sentence reply that: "
            "(1) acknowledges their interest without over-excitement, "
            "(2) asks one qualifying question OR proposes a specific 15-min call time, "
            "(3) reiterates the immediate next step (sample report or call). "
            "Sound like a real person, not a sales script."
        )
    elif intent == "question":
        instruction = (
            "The prospect asked a question. Answer it directly and completely in 2–3 sentences. "
            "Then add one soft CTA to move forward (sample report or short call). "
            "Do not hedge. Do not over-explain EchoFrame. Just answer and advance."
        )
    else:
        return ""

    response = client.messages.create(
        model=cfg.claude_model,
        max_tokens=300,
        system=(
            "You are Jacob Starling. Write like a human financial professional, "
            "not a sales rep. Short, direct, no fluff."
        ),
        messages=[{
            "role": "user",
            "content": f"""CONTEXT:
Original email sent to {first_name} ({industry} business owner):
{original_email_body[:500]}

Their reply:
{reply_body[:500]}

Intent classified as: {intent}

Instruction: {instruction}

Write only the reply body. No subject line. Sign off as 'Jacob'.""",
        }],
    )

    return response.content[0].text.strip()
