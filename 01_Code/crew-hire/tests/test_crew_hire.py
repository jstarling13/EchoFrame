"""Crew Hire tests — pure logic, booker mocked, no external calls."""

import os
import sys
from datetime import datetime

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine
import api


def _job(**kw):
    return engine.JobRequirement(
        kw.pop("title", "HVAC Tech"),
        required_skills=kw.pop("required_skills", ["hvac", "epa 608"]),
        preferred_skills=kw.pop("preferred_skills", ["commercial"]),
        min_years_experience=kw.pop("min_years_experience", 2),
        requires_license=kw.pop("requires_license", "driver's license"),
        qualify_threshold=kw.pop("qualify_threshold", 60),
    )


# ── knockouts ────────────────────────────────────────────────────────────────

def test_missing_required_skill_disqualifies():
    r = engine.screen_applicant(
        engine.Applicant("X", 8, ["hvac"], ["driver's license"]), _job())
    assert r.qualified is False
    assert any("required skill" in reason.lower() for reason in r.reasons)


def test_missing_license_disqualifies():
    r = engine.screen_applicant(
        engine.Applicant("X", 8, ["hvac", "epa 608"], []), _job())
    assert r.qualified is False
    assert any("license" in reason.lower() for reason in r.reasons)


def test_unavailable_disqualifies():
    r = engine.screen_applicant(
        engine.Applicant("X", 8, ["hvac", "epa 608"], ["driver's license"], available=False),
        _job())
    assert r.qualified is False


def test_strong_candidate_qualifies():
    r = engine.screen_applicant(
        engine.Applicant("X", 5, ["hvac", "epa 608", "commercial"], ["driver's license"]),
        _job())
    assert r.qualified is True
    assert r.score >= 60


def test_case_insensitive_skill_match():
    r = engine.screen_applicant(
        engine.Applicant("X", 5, ["HVAC", "EPA 608", "Commercial"], ["Driver's License"]),
        _job())
    assert r.qualified is True


def test_low_experience_lowers_score_but_may_still_note():
    r = engine.screen_applicant(
        engine.Applicant("X", 1, ["hvac", "epa 608"], ["driver's license"]), _job())
    assert any("experience" in reason.lower() for reason in r.reasons)


# ── screen_and_book ────────────────────────────────────────────────────────────

def test_ranking_and_booking():
    job = _job()
    applicants = [
        engine.Applicant("Top", 6, ["hvac", "epa 608", "commercial"], ["driver's license"]),
        engine.Applicant("Mid", 2, ["hvac", "epa 608"], ["driver's license"]),
        engine.Applicant("Out", 8, ["hvac"], ["driver's license"]),   # missing epa 608
    ]
    result = engine.screen_and_book(applicants, job, slots_start=datetime(2026, 6, 3, 10, 0))
    assert result["qualified_count"] == 2
    assert result["qualified"][0].name == "Top"          # highest score first
    assert all(r.interview_slot for r in result["qualified"])  # booked
    assert len(result["booker"].booked) == 2
    assert any(r.name == "Out" for r in result["rejected"])


def test_interview_slots_skip_weekends():
    # 2026-06-06 is a Saturday; first slot should land on Monday 2026-06-08
    slots = engine._interview_slots(datetime(2026, 6, 6, 10, 0), 1)
    first = datetime.fromisoformat(slots[0])
    assert first.weekday() < 5


def test_render_summary_runs():
    job = _job()
    result = engine.screen_and_book(
        [engine.Applicant("Top", 6, ["hvac", "epa 608"], ["driver's license"])],
        job, slots_start=datetime(2026, 6, 3, 10, 0))
    assert "CREW HIRE" in engine.render_summary(result)


# ── API ────────────────────────────────────────────────────────────────────────

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_api_screen():
    r = client.post("/api/screen", json={
        "job": {
            "title": "HVAC Tech", "required_skills": ["hvac", "epa 608"],
            "preferred_skills": ["commercial"], "min_years_experience": 2,
            "requires_license": "driver's license", "qualify_threshold": 60,
        },
        "applicants": [
            {"name": "Top", "years_experience": 6,
             "skills": ["hvac", "epa 608", "commercial"], "licenses": ["driver's license"]},
            {"name": "Out", "years_experience": 8, "skills": ["hvac"],
             "licenses": ["driver's license"]},
        ],
        "slots_start": "2026-06-03T10:00:00",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["qualified_count"] == 1
    assert body["qualified"][0]["name"] == "Top"
    assert body["qualified"][0]["interview_slot"]
    assert "CREW HIRE" in body["summary"]


def test_api_rejects_bad_threshold():
    r = client.post("/api/screen", json={
        "job": {"title": "X", "qualify_threshold": 150},
        "applicants": [],
    })
    assert r.status_code == 422
