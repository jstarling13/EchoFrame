"""
Crew Hire — applicant screening & interview-booking engine
─────────────────────────────────────────────────────────────────────────────
Core promise (from ops/ironhire.html):
  "You only sit down with candidates who are pre-qualified, pre-screened, and
   actually showed up to the interview."
  1. Tell us who you're looking for
  2. We screen and filter the applicants
  3. Qualified candidates land on your calendar  (multi-board posting,
     pre-screening & qualification, confirmed interview booking, candidate tracking)

Pure Python. Job-board posting and calendar/SMS confirmation are INJECTED/mocked —
nothing is posted or sent. This module is the "score, knock out, rank, and book the
qualified ones" core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional


@dataclass
class JobRequirement:
    title: str
    required_skills: list[str] = field(default_factory=list)   # hard knockouts
    preferred_skills: list[str] = field(default_factory=list)  # scored bonus
    min_years_experience: float = 0.0
    requires_license: Optional[str] = None                     # e.g. "CDL"; hard knockout
    qualify_threshold: float = 60.0                            # score needed to qualify


@dataclass
class Applicant:
    name: str
    years_experience: float = 0.0
    skills: list[str] = field(default_factory=list)
    licenses: list[str] = field(default_factory=list)
    available: bool = True


@dataclass
class ScreenResult:
    name: str
    score: float                 # 0-100
    qualified: bool
    reasons: list[str]           # why qualified / disqualified
    interview_slot: Optional[str] = None


def _norm(items: list[str]) -> set[str]:
    return {s.strip().lower() for s in items if s and s.strip()}


def screen_applicant(applicant: Applicant, job: JobRequirement) -> ScreenResult:
    """Score one applicant against the job. Hard knockouts force qualified=False."""
    reasons: list[str] = []
    app_skills = _norm(applicant.skills)
    req_skills = _norm(job.required_skills)
    pref_skills = _norm(job.preferred_skills)
    app_licenses = _norm(applicant.licenses)

    knocked_out = False

    # Hard knockout: missing a required skill
    missing_required = req_skills - app_skills
    if missing_required:
        knocked_out = True
        reasons.append("Missing required skill(s): " + ", ".join(sorted(missing_required)) + ".")

    # Hard knockout: missing required license
    if job.requires_license and job.requires_license.strip().lower() not in app_licenses:
        knocked_out = True
        reasons.append(f"Missing required license: {job.requires_license}.")

    # Hard knockout: not available
    if not applicant.available:
        knocked_out = True
        reasons.append("Not currently available.")

    # ── Scoring (0-100) ────────────────────────────────────────────────────────
    # Required skills coverage: 50 pts
    req_cover = 1.0 if not req_skills else len(req_skills & app_skills) / len(req_skills)
    score = 50.0 * req_cover

    # Experience vs minimum: 30 pts (capped at 2x the minimum, or full if no minimum)
    if job.min_years_experience > 0:
        exp_ratio = min(applicant.years_experience / job.min_years_experience, 2.0) / 2.0
        score += 30.0 * exp_ratio
        if applicant.years_experience < job.min_years_experience:
            reasons.append(
                f"Below preferred experience ({applicant.years_experience:g}y "
                f"< {job.min_years_experience:g}y)."
            )
    else:
        score += 30.0

    # Preferred skills: 20 pts
    if pref_skills:
        score += 20.0 * (len(pref_skills & app_skills) / len(pref_skills))
    else:
        score += 20.0

    score = round(max(0.0, min(100.0, score)), 1)

    qualified = (not knocked_out) and score >= job.qualify_threshold
    if qualified:
        reasons.insert(0, f"Qualified (score {score:.0f} ≥ {job.qualify_threshold:.0f}).")
    elif not knocked_out:
        reasons.append(f"Score {score:.0f} below qualify threshold {job.qualify_threshold:.0f}.")

    return ScreenResult(name=applicant.name, score=score, qualified=qualified, reasons=reasons)


# Booker: (candidate_name, slot_iso) -> True on success. Mock by default.
Booker = Callable[[str, str], bool]


def _mock_booker_factory():
    booked: list[dict] = []

    def booker(name: str, slot_iso: str) -> bool:
        booked.append({"name": name, "slot": slot_iso})
        return True

    booker.booked = booked  # type: ignore[attr-defined]
    return booker


def _interview_slots(start: datetime, count: int) -> list[str]:
    """Generate `count` interview slots, weekdays 10:00 onward, hourly, skipping weekends."""
    slots: list[str] = []
    cur = start.replace(hour=10, minute=0, second=0, microsecond=0)
    while len(slots) < count:
        if cur.weekday() < 5 and 10 <= cur.hour < 16:
            slots.append(cur.isoformat())
            cur += timedelta(hours=1)
        else:
            # jump to next day 10:00
            cur = (cur + timedelta(days=1)).replace(hour=10)
    return slots


def screen_and_book(applicants: list[Applicant], job: JobRequirement, *,
                    slots_start: Optional[datetime] = None,
                    booker: Optional[Booker] = None) -> dict:
    """Screen all applicants, rank qualified ones, and book interview slots for them."""
    booker = booker or _mock_booker_factory()
    results = [screen_applicant(a, job) for a in applicants]

    qualified = sorted((r for r in results if r.qualified),
                       key=lambda r: r.score, reverse=True)
    rejected = [r for r in results if not r.qualified]

    slots = _interview_slots(slots_start or datetime.now(), len(qualified))
    for r, slot in zip(qualified, slots):
        if booker(r.name, slot):
            r.interview_slot = slot

    return {
        "job_title": job.title,
        "applicant_count": len(results),
        "qualified_count": len(qualified),
        "qualified": qualified,
        "rejected": rejected,
        "all_results": results,
        "booker": booker,
    }


def render_summary(result: dict) -> str:
    lines = [f"CREW HIRE — SCREENING SUMMARY · {result['job_title']}",
             f"{result['applicant_count']} applicants screened · "
             f"{result['qualified_count']} qualified and booked.", ""]
    if result["qualified"]:
        lines.append("QUALIFIED (on your calendar):")
        for r in result["qualified"]:
            slot = r.interview_slot or "unscheduled"
            lines.append(f"  • {r.name} — score {r.score:.0f} — interview {slot}")
        lines.append("")
    if result["rejected"]:
        lines.append("SCREENED OUT:")
        for r in result["rejected"]:
            lines.append(f"  • {r.name} (score {r.score:.0f}): {r.reasons[-1]}")
    return "\n".join(lines)
