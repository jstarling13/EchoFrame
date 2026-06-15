# Crew Hire (MVP)

> *"You only sit down with candidates who are pre-qualified, pre-screened, and actually showed
> up to the interview."* — `echoframe-site/ops/ironhire.html`

Crew Hire screens applicants against a job's requirements, knocks out the ones who don't meet
hard criteria, scores and ranks the rest, and books interview slots for the qualified candidates.

Job-board posting and calendar/SMS confirmation are **mocked** — nothing is posted or sent.
Those integrations are the documented seam; this MVP is the **screening + ranking + booking** core.

## What it does
- **Hard knockouts:** missing a required skill, missing a required license, or not available.
- **0–100 score:** required-skill coverage (50) + experience vs minimum (30) + preferred skills (20).
- Qualifies candidates at/above a configurable threshold; ranks them by score.
- Books interview slots (weekday business hours, skips weekends) via an injected booker.
- Returns qualified (with slots), rejected (with reasons), and a readable summary.

## Run it

```powershell
cd 01_Code\crew-hire
pip install -r requirements.txt

python demo.py                         # offline screening summary
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8018   # HTTP API
```

### API
- `GET  /health`
- `POST /api/screen`:

```json
{
  "job": {
    "title": "HVAC Service Technician",
    "required_skills": ["hvac", "epa 608"], "preferred_skills": ["commercial"],
    "min_years_experience": 2, "requires_license": "driver's license", "qualify_threshold": 60
  },
  "applicants": [
    {"name": "Alex Stone", "years_experience": 5, "skills": ["hvac", "epa 608", "commercial"], "licenses": ["driver's license"]}
  ],
  "slots_start": "2026-06-03T10:00:00"
}
```

Returns ranked qualified candidates (with booked interview slots), rejected candidates with
reasons, the (mock) bookings, and a summary.

## Assumptions / scope
- **Multi-board job posting and the actual calendar/SMS confirmation are mocked** (the documented
  integration seam). Applicants are provided to the engine; in production they arrive from the job
  boards. The screening/scoring/booking logic is the real value here.
- The scoring weights are sensible defaults; they're easy to tune per trade.
- "Actually showed up" (confirmation/no-show handling) is a follow-up layer over the booker — not
  built in this MVP (would reuse the Call Catch / sequence sender pattern).
- No auth/billing/persistence. Informational/automation aid only.
