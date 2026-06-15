"""
frameworks.py — Behavioral psychology frameworks for persuasive email generation.

Each framework is a structured set of instructions that gets injected into
the LLM prompt when writing cold outreach copy.

References:
  - Cialdini, R. (2001). Influence: The Psychology of Persuasion.
  - Fogg, B.J. (2009). A Behavior Model for Persuasive Design.
  - Kahneman, D. (2011). Thinking, Fast and Slow.
  - Ariely, D. (2008). Predictably Irrational.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass
class PsychFramework:
    name: str
    trigger_condition: str          # When to use this framework
    email_directives: list[str]     # Specific instructions for the LLM
    forbidden_patterns: list[str]   # Things that break this framework
    example_subject_patterns: list[str]
    example_opening_patterns: list[str]


# ─── Framework Definitions ────────────────────────────────────────────────────

LOSS_AVERSION_AUTHORITY = PsychFramework(
    name="loss_aversion_authority",
    trigger_condition="Use for risk-averse SMB owners (HVAC, plumbing, electrical, roofing). "
                      "These owners built their business with their hands and are terrified of "
                      "losing what they've built. Authority figures (analysts, finance professionals) "
                      "reduce their perceived risk.",
    email_directives=[
        # Loss Aversion (Kahneman/Tversky): losses feel 2x worse than equivalent gains
        "Frame the value proposition as PREVENTING LOSS, not achieving gain. "
        "Don't say 'discover $1,200 in savings.' Say 'stop the $1,200/month that's leaking out right now.'",

        "Include a specific, concrete loss scenario anchored to their industry. "
        "For HVAC: 'Most HVAC owners are losing $200–400/month in their misc expense bucket without knowing it.' "
        "For restaurants: 'Your food cost percentage is probably 2–3 points higher than it should be — "
        "that's $800–1,200/month on a $40k/month revenue base.'",

        "Use the word 'leaking' instead of 'opportunity.' Leaks are losses already happening. "
        "Opportunities are optional. Leaks are urgent.",

        # Cialdini Authority: people follow credible experts
        "Establish Jacob's credibility in the first 2 sentences. "
        "Mention Master of Finance (Emory) OR Investment Analyst at Blue Eagle Capital — not both. "
        "Do NOT use 'I'm an expert' — show it through specificity (numbers, industry benchmarks).",

        "Reference a specific industry benchmark number to demonstrate insider knowledge. "
        "Example: 'HVAC labor cost benchmarks for companies your size run 28–34% of revenue. "
        "Most owners I look at are running 36–40% and don't know it.'",

        # Cialdini Scarcity/Urgency (use sparingly — only in follow-up steps)
        "In steps 3–5 only: add a soft scarcity signal. "
        "'I only take on 5 new clients per month to keep turnaround under 48 hours.' "
        "This must feel like a real operational constraint, not a fake deadline.",
    ],
    forbidden_patterns=[
        "game-changing", "revolutionary", "synergies", "leverage", "solution",
        "I wanted to reach out", "I hope this email finds you well",
        "I know you're busy", "just checking in",
        "unprecedented", "cutting-edge",
        "every owner I talk to", "every business owner", "most owners I talk to",
        "owners always tell me", "I hear this all the time",
    ],
    example_subject_patterns=[
        "[Company] labor cost — quick question",
        "HVAC misc expenses — Columbus owner",
        "Your financials flagged something",
        "Found something in your numbers, [First]",
    ],
    example_opening_patterns=[
        "Most HVAC companies your size are losing $200–400/month in their misc expense bucket. "
        "It doesn't show up on the P&L as a single line — it hides in a dozen small categories "
        "nobody audits.",

        "I looked at benchmarks for [industry] businesses with [X] employees in [city]. "
        "The average [expense type] ratio runs [X]%. If you're above that, "
        "you're leaving real money on the table every month.",
    ],
)


SOCIAL_PROOF_OPPORTUNITY = PsychFramework(
    name="social_proof_opportunity",
    trigger_condition="Use for growth-focused operators (restaurants, salons, agencies) "
                      "who are expansion-minded and motivated by what peers are doing. "
                      "They want to know what successful operators know that they don't.",
    email_directives=[
        # Cialdini Social Proof: people follow what peers do
        "Open with what similar businesses in their category have discovered or done. "
        "Use specific examples: 'A Columbus restaurant owner found that his food cost percentage "
        "had crept from 31% to 37% over 8 months — invisible until it was benchmarked.'",

        "Position EchoFrame as 'what the operators who are growing are doing.' "
        "Not 'a service you should buy' but 'what the people ahead of you are already using.'",

        "Name the peer group specifically — not 'other business owners' but "
        "'other Columbus restaurant owners' or 'salon owners in the $30–60k/month revenue range.'",

        # Opportunity framing (for growth-minded personas)
        "Frame the insight as competitive intelligence, not financial hygiene. "
        "'Knowing your numbers isn't accounting — it's knowing where to put your next dollar.'",

        # Cialdini Liking: similarity increases persuasion
        "Reference Columbus GA or their specific city. Local familiarity reduces skepticism. "
        "'I work primarily with [city] service businesses because the market dynamics here "
        "are different from Atlanta.'",
    ],
    forbidden_patterns=[
        "I hope this finds you well", "just following up", "touching base",
        "synergy", "leverage", "scale", "game-changing",
        "10x", "crush it", "dominate",
    ],
    example_subject_patterns=[
        "What Columbus restaurant owners are seeing in their numbers",
        "Salon benchmark — [City] market",
        "[First], a question about your margins",
    ],
    example_opening_patterns=[
        "I work with a handful of [industry] operators in [city]. "
        "The ones who are opening second locations are all doing one thing differently: "
        "they know their cost structure at the line-item level, not just the total.",
    ],
)


TIME_SAVING_SIMPLICITY = PsychFramework(
    name="time_saving_simplicity",
    trigger_condition="Use for time-starved solo founders and operators with 1–3 employees. "
                      "These people are drowning and their primary objection is 'I don't have time.' "
                      "Every sentence must be shorter. Complexity is the enemy.",
    email_directives=[
        # Fogg Behavior Model: Behavior = Motivation × Ability × Prompt
        # For time-starved personas, Ability (ease) is the bottleneck
        "Make the process sound trivially easy. The EXACT steps: "
        "(1) Export your expenses to CSV. (2) Upload it. (3) Get the report in your email in 48 hours. "
        "Spell out each step. Show that it's 5 minutes of their time, max.",

        "Use the subject line to quantify time. '5 minutes → [outcome]' format. "
        "Examples: '5-minute upload. Full financial picture.' or 'One CSV file. Here's what it shows.'",

        # Loss aversion adapted for time-poor people: they lose time AND money
        "The primary loss to highlight is TIME wasted trying to understand the numbers themselves. "
        "'You didn't start a business to become an accountant. You started it to [do their craft].'",

        # Fogg: reduce friction in the prompt/CTA
        "The call to action must be the lowest-friction possible. "
        "Don't ask for a call. Offer to send a free sample report first. "
        "'Reply yes and I'll send you a sample report for an HVAC company exactly your size.'",

        "Emails must be 6 sentences or fewer. No paragraphs longer than 2 sentences. "
        "White space is persuasion for time-starved readers.",
    ],
    forbidden_patterns=[
        "comprehensive", "in-depth", "detailed analysis", "robust", "complex",
        "I wanted to reach out to introduce", "I hope this email finds you",
        "schedule a call", "book a demo", "let's connect",
    ],
    example_subject_patterns=[
        "5 minutes → full financial picture",
        "One CSV file. Here's what it shows.",
        "[First] — your expense leaks (2 min read)",
    ],
    example_opening_patterns=[
        "You didn't start an HVAC company to become an accountant. "
        "I'll handle the numbers. You get a plain-English report by email.",

        "Upload one CSV. I do the rest. "
        "You get a Word doc showing your top 5 cost leaks, your health score, "
        "and one thing to fix this quarter.",
    ],
)


# ─── Framework Registry ───────────────────────────────────────────────────────

FRAMEWORKS: dict[str, PsychFramework] = {
    "loss_aversion_authority": LOSS_AVERSION_AUTHORITY,
    "social_proof_opportunity": SOCIAL_PROOF_OPPORTUNITY,
    "time_saving_simplicity": TIME_SAVING_SIMPLICITY,
}

# Maps persona types (from scorer.py) to primary + fallback frameworks
PERSONA_FRAMEWORK_MAP: dict[str, tuple[str, str]] = {
    "risk_averse_smb_owner":   ("loss_aversion_authority",   "time_saving_simplicity"),
    "growth_focused_operator": ("social_proof_opportunity",  "loss_aversion_authority"),
    "time_starved_founder":    ("time_saving_simplicity",    "loss_aversion_authority"),
}


def get_framework(persona_type: str, use_fallback: bool = False) -> PsychFramework:
    """Returns the appropriate psych framework for a given persona."""
    primary, fallback = PERSONA_FRAMEWORK_MAP.get(
        persona_type,
        ("loss_aversion_authority", "time_saving_simplicity"),
    )
    key = fallback if use_fallback else primary
    return FRAMEWORKS[key]


def get_framework_for_sequence_step(persona_type: str, step: int) -> PsychFramework:
    """
    Varies the framework across the sequence to avoid psychological monotony.

    Steps 1–2: Primary framework (hook with the core emotional lever)
    Steps 3–4: Add social proof regardless of persona (builds cumulative trust)
    Step 5:    Breakup email — minimal framework, pure directness
    """
    if step <= 2:
        return get_framework(persona_type, use_fallback=False)
    elif step <= 4:
        # Social proof mid-sequence increases cumulative trust
        return FRAMEWORKS["social_proof_opportunity"]
    else:
        # Breakup: no framework — just honest directness
        return get_framework(persona_type, use_fallback=True)
