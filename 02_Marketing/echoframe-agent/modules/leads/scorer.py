"""
scorer.py — Lead scoring engine (0–100 scale).

Scoring is intentionally simple and transparent — no black box.
Each signal has an explicit weight and a reason why it matters for EchoFrame.

High-value signals for EchoFrame specifically:
  - Verified email (no email = no outreach)
  - Owner/Founder title (decision maker, not gatekeeper)
  - Industry match (home services >> restaurants >> salons for conversion rate)
  - Company size 2–20 (solo operators don't pay for reports; 50+ have CFOs)
  - Local geography (Columbus GA / Phenix City / Auburn — Jacob has local credibility)
  - Phone available (signals they're reachable for follow-up calls)
"""

from dataclasses import dataclass
from .apollo_client import RawLead
from config import cfg


# Scoring weights — all weights must sum naturally; no normalization needed
# because the ceiling is enforced at 100.
WEIGHTS = {
    "has_verified_email": 30,       # no email = literally cannot contact them
    "is_decision_maker": 20,        # owner/founder title = no selling through gatekeepers
    "is_priority_industry": 15,     # HVAC/plumbing/electrical convert best for EchoFrame
    "is_local": 15,                 # Columbus GA area — Jacob's home turf advantage
    "company_size_sweet_spot": 10,  # 2–20 employees is EchoFrame's ideal size band
    "has_phone": 10,                # phone = can do call close after email warm-up
}

PRIORITY_INDUSTRIES = {
    "hvac", "plumbing", "electrical", "roofing", "landscaping",
    "heating and cooling", "air conditioning",
}

DECISION_MAKER_TITLES = {
    "owner", "founder", "co-owner", "co-founder", "president", "ceo",
    "proprietor", "managing partner",
}

LOCAL_CITIES = {
    "columbus", "phenix city", "auburn", "opelika",
    "fortson", "midland", "harris county", "muscogee",
}


@dataclass
class ScoredLead:
    raw: RawLead
    score: float
    signals: dict  # which signals fired and their contribution
    persona_type: str


def _is_decision_maker(title: str | None) -> bool:
    t = (title or "").lower()
    return any(dm in t for dm in DECISION_MAKER_TITLES)


def _is_priority_industry(industry: str) -> bool:
    i = industry.lower()
    return any(pi in i for pi in PRIORITY_INDUSTRIES)


def _is_local(city: str, state: str) -> bool:
    city_lower = city.lower()
    state_lower = state.lower()
    if state_lower in ("ga", "georgia", "al", "alabama"):
        return any(lc in city_lower for lc in LOCAL_CITIES)
    return False


def _company_size_sweet_spot(count: int) -> bool:
    return 2 <= count <= 20


def _assign_persona(lead: RawLead) -> str:
    """
    Maps a lead to a behavioral persona that drives which psych framework to use.

    Personas:
      - risk_averse_smb_owner: Most home service owners. Scared of losing money.
        → Use loss aversion + authority (Cialdini)
      - growth_focused_operator: Restaurant/salon owners expanding locations.
        → Use social proof + opportunity framing
      - time_starved_founder: Solo operator, extreme time scarcity.
        → Use time-saving heuristics + simplicity (Fogg)
    """
    industry = (lead.industry or "").lower()
    size = lead.employee_count or 0
    title = (lead.title or "").lower()

    if _is_priority_industry(industry) and size <= 10:
        return "risk_averse_smb_owner"
    elif "restaurant" in industry or "food" in industry:
        return "growth_focused_operator"
    elif size <= 3 or "solo" in title:
        return "time_starved_founder"
    else:
        return "risk_averse_smb_owner"  # safe default for EchoFrame's market


def score_lead(lead: RawLead) -> ScoredLead:
    signals = {}
    total = 0.0

    if lead.has_verified_email:
        signals["has_verified_email"] = WEIGHTS["has_verified_email"]
        total += WEIGHTS["has_verified_email"]

    if _is_decision_maker(lead.title):
        signals["is_decision_maker"] = WEIGHTS["is_decision_maker"]
        total += WEIGHTS["is_decision_maker"]

    if _is_priority_industry(lead.industry):
        signals["is_priority_industry"] = WEIGHTS["is_priority_industry"]
        total += WEIGHTS["is_priority_industry"]

    if _is_local(lead.city, lead.state):
        signals["is_local"] = WEIGHTS["is_local"]
        total += WEIGHTS["is_local"]

    if _company_size_sweet_spot(lead.employee_count):
        signals["company_size_sweet_spot"] = WEIGHTS["company_size_sweet_spot"]
        total += WEIGHTS["company_size_sweet_spot"]

    if lead.has_phone:
        signals["has_phone"] = WEIGHTS["has_phone"]
        total += WEIGHTS["has_phone"]

    persona = _assign_persona(lead)

    return ScoredLead(
        raw=lead,
        score=min(total, 100.0),
        signals=signals,
        persona_type=persona,
    )


GENERIC_EMAIL_PREFIXES = {"contact", "info", "hello", "admin", "support", "office", "mail", "team", "ambiance"}

# Titles that are definitely NOT decision makers — disqualify regardless of score
DISQUALIFIED_TITLES = {
    "account executive", "sales director", "vice president", "vp ",
    "client experience", "general manager", "pastry chef", "model",
    "electrical maintenance", "team member", "associate", "coordinator",
    "receptionist", "assistant", "technician", "analyst", "engineer",
}


def _is_generic_email(email: str) -> bool:
    prefix = email.split("@")[0].lower()
    return prefix in GENERIC_EMAIL_PREFIXES


def _is_disqualified_title(title: str | None) -> bool:
    t = (title or "").lower()
    return any(bad in t for bad in DISQUALIFIED_TITLES)


def score_and_rank(leads: list[RawLead], min_score: float = 40.0) -> list[ScoredLead]:
    """
    Scores all leads, filters out below threshold, returns sorted descending.
    Also drops generic inbox emails (contact@, info@, etc.) — they never reach an owner.
    """
    scored = [score_lead(lead) for lead in leads]
    qualified = [
        s for s in scored
        if s.score >= min_score
        and not _is_generic_email(s.raw.email)
        and not _is_disqualified_title(s.raw.title)
    ]
    return sorted(qualified, key=lambda s: s.score, reverse=True)
