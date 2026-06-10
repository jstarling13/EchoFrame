"""Crew Hire — offline demo. Run: python demo.py"""

from datetime import datetime

import engine


def main() -> int:
    job = engine.JobRequirement(
        title="HVAC Service Technician",
        required_skills=["hvac", "epa 608"],
        preferred_skills=["commercial", "electrical"],
        min_years_experience=2,
        requires_license="driver's license",
        qualify_threshold=60,
    )
    applicants = [
        engine.Applicant("Alex Stone", 5, ["hvac", "epa 608", "commercial", "electrical"],
                         ["driver's license"]),
        engine.Applicant("Brooke Lee", 1, ["hvac", "epa 608"], ["driver's license"]),
        engine.Applicant("Cory Diaz", 8, ["hvac"], ["driver's license"]),   # missing EPA 608
        engine.Applicant("Dev Patel", 4, ["hvac", "epa 608", "commercial"], []),  # no license
        engine.Applicant("Erin Fox", 3, ["hvac", "epa 608"], ["driver's license"],
                         available=False),
    ]

    result = engine.screen_and_book(applicants, job,
                                    slots_start=datetime(2026, 6, 3, 10, 0))
    print(engine.render_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
