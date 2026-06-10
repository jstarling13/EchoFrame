"""Offline demo for Crew Hire. python demo_crew_hire.py"""
from pathlib import Path
from crew_hire_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "crew_hire_sample_input.csv"

PROSE = {
    "screening_note": (
        "Every applicant was scored against the five must-haves you set for this requisition. Candidates "
        "missing any hard requirement were screened out automatically; the rest were ranked on depth of match. "
        "<b>Score weighting:</b> hands-on heavy-duty experience (30), engine-platform breadth (25), "
        "certifications &amp; CDL (20), reliability signals — tenure and references (15), and tooling/availability (10)."
    ),
    "criteria": [
        "<b>Minimum 3 years</b> hands-on heavy-duty diesel repair",
        "Demonstrated <b>Cummins and/or Detroit</b> engine work",
        "Valid driver's license; <b>CDL-A preferred, not required</b>",
        "Can pass <b>DOT physical and background</b> screen",
        "Available to start within <b>3 weeks</b>",
    ],
    "one_thing_title": "Prioritize CAND-2207 — and move fast.",
    "one_thing_body": (
        "It's the strongest match on the board: <span class=\"hl\">7 years</span> of heavy-duty experience, a "
        "current <span class=\"hl\">CDL-A</span>, certified on both Cummins and Detroit platforms, and the only "
        "qualified candidate who already owns their tooling and is DOT-inspection certified — a "
        "<span class=\"hl\">94/100</span> against your rubric. A tech this complete won't stay on the market long "
        "in Columbus; their interview is first up Tuesday at 9:00 AM. Be ready to extend a same-week offer if it "
        "goes well, and have a number prepared before they walk in."
    ),
}


def main():
    print(f"  crew-hire -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
