"""
Crew Hire — FastAPI wrapper.  Run:  uvicorn api:app --reload --port 8018
Job-board posting and calendar booking are mocked — nothing is posted or sent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

import engine

app = FastAPI(title="Crew Hire", version="0.1.0")


class JobIn(BaseModel):
    title: str = Field(..., max_length=200)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_years_experience: float = Field(0.0, ge=0)
    requires_license: Optional[str] = None
    qualify_threshold: float = Field(60.0, ge=0, le=100)


class ApplicantIn(BaseModel):
    name: str = Field(..., max_length=200)
    years_experience: float = Field(0.0, ge=0)
    skills: list[str] = Field(default_factory=list)
    licenses: list[str] = Field(default_factory=list)
    available: bool = True


class ScreenIn(BaseModel):
    job: JobIn
    applicants: list[ApplicantIn]
    slots_start: Optional[str] = Field(None, description="ISO datetime for first interview slot")


def _result_to_dict(r: engine.ScreenResult) -> dict:
    return {
        "name": r.name, "score": r.score, "qualified": r.qualified,
        "reasons": r.reasons, "interview_slot": r.interview_slot,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/screen")
def screen(payload: ScreenIn) -> dict:
    job = engine.JobRequirement(
        title=payload.job.title, required_skills=payload.job.required_skills,
        preferred_skills=payload.job.preferred_skills,
        min_years_experience=payload.job.min_years_experience,
        requires_license=payload.job.requires_license,
        qualify_threshold=payload.job.qualify_threshold,
    )
    applicants = [
        engine.Applicant(name=a.name, years_experience=a.years_experience,
                         skills=a.skills, licenses=a.licenses, available=a.available)
        for a in payload.applicants
    ]
    start = datetime.fromisoformat(payload.slots_start) if payload.slots_start else None
    result = engine.screen_and_book(applicants, job, slots_start=start)
    return {
        "job_title": result["job_title"],
        "applicant_count": result["applicant_count"],
        "qualified_count": result["qualified_count"],
        "qualified": [_result_to_dict(r) for r in result["qualified"]],
        "rejected": [_result_to_dict(r) for r in result["rejected"]],
        "booked": getattr(result["booker"], "booked", []),
        "summary": engine.render_summary(result),
    }
