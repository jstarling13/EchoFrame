# EchoFrame Product Status Audit

**Audited:** 2026-06-02 (overnight autonomous engineering run)
**Auditor:** Claude (Opus 4.8), autonomous overnight engineer
**Method:** Read every marketing product page (the spec) + the `echoframe-backend` source and tests.

> **Brutal-honesty note.** The starting brief said "the only product with real code is Clarity
> Report, and it works." That was *half* true. Clarity Report has a large, mature, well-tested
> codebase — but the working copy of `engine.py` was **truncated mid-function** (`_set_cell_bg`
> cut off at an unterminated string literal on the last line), so the backend **would not even
> import** and **all 75 tests errored at collection**. The committed `HEAD` copy is truncated at
> the identical spot. The engine had clearly run before (there are dozens of generated `.docx`
> reports dated 2026-05-31 in `reports/`), so the truncation happened after those were produced.
> I completed the missing function (standard python-docx shading helper); all 75 tests now pass.
> See `OVERNIGHT_LOG.md` for detail.

---

## Summary table

| # | Product | Page | Code exists? | State | One-line core promise |
|---|---------|------|--------------|-------|------------------------|
| 1 | **Clarity Report** (flagship) | — (backend) | ✅ yes | **working → production-ready** (after fix) | CSV → benchmarked P&L analysis → narrated .docx emailed monthly |
| 2 | Auto Ledger | intelligence/vericount.html | ❌ no | none | Bank/card transactions auto-categorized with plain-English notes + monthly summary |
| 3 | Rate Watch | intelligence/oryn.html | ❌ no | none → **MVP built (this run)** | Benchmark vendor spend vs market, flag overpays, alert before renewals |
| 4 | Rival Scan | intelligence/veris.html | ❌ no | none | Monitor competitor pricing/reviews/promos daily, morning change alerts |
| 5 | Shift Lens | intelligence/strata.html | ❌ no | none → **MVP built (this run)** | Per-shift labor-cost-vs-revenue P&L, flag unprofitable shifts |
| 6 | Permit Watch | ops/permitwatch.html | ❌ no | none → **MVP built (this run)** | One dashboard of licenses/permits with 30-day expiry alerts |
| 7 | Bay Coach | ops/baysignal.html | ❌ no | none | Surface the right service recommendation at write-up from vehicle history/mileage |
| 8 | Call Catch | revenue/missedcall.html | ❌ no | none | Auto-text the second a call is missed, keep the lead warm |
| 9 | Quote Revive | revenue/quoterevive.html | ❌ no | none | Auto follow-up sequence on ghosted quotes/cold leads |
| 10 | Clear Ledger | revenue/clearledger.html | ❌ no | none | Invoice dunning sequence from first nudge to final notice + human handoff |
| 11 | Call Router | ops/traderelay.html | ❌ no | none | 24/7 answer, qualify, and route inbound calls to the right tech |
| 12 | Crew Hire | ops/ironhire.html | ❌ no | none | Post jobs, screen/qualify applicants, book confirmed interviews |
| 13 | Drive Pay | ops/hydropay.html | ❌ no | none | Text-to-pay link before the car leaves the lot + status tracking |

State legend: **none** (no code) · **stub** (skeleton only) · **partial** (some features) · **working** (core works end-to-end) · **production-ready** (working + validated + tested + documented).

---

## 1. Clarity Report — flagship (`echoframe-backend/`)

**Code:** FastAPI (`main.py`) + analysis engine (`engine.py`, ~2.7k lines) + 75 security/behaviour
tests (`tests/test_security.py`). There is also a Node `server.js`/`package.json` present (a Stripe
Checkout front used in production); the Python app is the report-generation core.

**Stack:** Stripe (payment gate) · Anthropic Claude haiku (prose only, via `tool_use`) ·
pandas (all math) · python-docx (document) · Resend (email) · matplotlib (charts) · slowapi (rate limit).

**What it does (verified by reading the code):**
1. Customer pays via Stripe Checkout; webhook records customer name/email.
2. Customer uploads a financial CSV to `/api/upload`; the endpoint verifies the Stripe session,
   validates email, enforces 5 MB / UTF-8 / `.csv` limits, then kicks off report generation.
3. Engine loads the CSV, computes revenue/expense ratios and **per-category variance vs industry
   benchmarks** (90+ industries hard-coded), ranks "leaks," computes a 0–100 health score.
4. Claude writes *only prose* (strict tool schema; numbers come from pandas, never the LLM).
   Heavy prompt-injection hardening + word-budget enforcement + output validation.
5. python-docx builds a 4-page branded report; Resend emails the `.docx`.

**Definition of "done MVP":** ✅ already exceeds MVP. Done = imports cleanly, all tests green,
input validation + payment gate solid, errors don't leak stack traces, a runnable local demo
exists, and setup is documented.

**State after this run: production-ready.**
- ✅ Fixed the import-blocking truncation in `engine.py`.
- ✅ 75/75 tests pass.
- ✅ Added `SETUP.md` (local run, env schema, test instructions).
- ✅ Added `demo_local.py` — generates a real `.docx` from a sample CSV with **all external
  calls mocked** (no Anthropic / Resend / Stripe calls, no email sent).
- ✅ Silenced the pytest-asyncio loop-scope deprecation warning (`pytest.ini`).

**Still owner's call (not blocking):** the in-memory Stripe idempotency store should become Redis
for multi-process deploys (already documented as a `PRODUCTION NOTE` in `main.py`); reports/uploads
are written to local disk (fine for single box, needs object storage at scale).

---

## 2–13. The 12 concept products

None had code. Each page is a clean, consistent spec (hero promise, 3-step "how it works",
4 feature cards, a price). Grouped by how they map to a buildable, **offline, mock-tested** MVP
in the flagship's Python/FastAPI style:

### Group A — pure-compute analytics (closest to flagship, highest ROI, easiest)
- **Rate Watch** ($99/mo): input vendors + what you pay → compare to market-rate band → rank
  overpayments in $ → flag renewals within 30 days. *Pure pandas, mirrors flagship benchmarking.*
- **Shift Lens** ($149/mo): shift rows (revenue, labor hours, wage) → per-shift profit & labor%
  → flag underperformers → schedule recommendations. *Pure pandas.*
- **Permit Watch** ($89/mo): items with expiry dates → days-until-expiry → 30-day alert digest.
  *Pure date math.*
- **Bay Coach** ($129/mo): vehicle mileage/history + service-interval rules → recommended services
  at write-up. *Rules engine.*

### Group B — follow-up / sequence messaging (share one engine, sender mocked)
- **Quote Revive** ($99/mo), **Clear Ledger** ($99/mo), **Call Catch** ($79/mo): all are
  "trigger → timed message sequence → escalate/handoff." A common sequence engine with a mocked
  SMS/email sender covers the core promise without real Twilio/Resend traffic.

### Group C — needs heavier external infra (telephony, scraping, payments) — MVP = engine only
- **Call Router** ($179/mo): voice answering/routing — real version needs a voice provider; MVP
  buildable = qualification + dispatch-rules engine over a transcript/JSON, mocked telephony.
- **Rival Scan** ($129/mo): competitor scraping — MVP = change-detection + alert digest over
  snapshot JSON, mocked fetch.
- **Crew Hire** ($149/mo): applicant screening/scoring + interview booking, mocked job boards.
- **Drive Pay** ($79/mo): Stripe payment-link generation (test-mode/mock) + payment status, mocked SMS.

**Definition of "done MVP" (applies to each):** runs locally with documented steps; the page's
single core promise works end-to-end on sample/mocked input; tests pass with all external services
mocked; `README.md` documents what it does, how to run, and assumptions; committed to the branch.

**Build order chosen for this run (depth over breadth):** Group A first (Rate Watch → Shift Lens →
Permit Watch → Bay Coach), because they are the highest-value, lowest-risk, fully-offline, and reuse
the flagship's proven "data in → pandas math → structured output" shape. Group B next if time allows.
Group C documented as designed-but-not-built where the external dependency dominates the value.

---

## Assumptions made during audit
- The marketing page copy is the authoritative spec (per the brief). Where a page implies a live
  integration (Plaid, Twilio, POS, scraping), the MVP delivers the **core computed/automated
  output** with that integration **mocked**, and documents the seam where the real integration plugs in.
- Prices on the pages are the intended monthly prices; MVPs don't implement billing (the flagship
  already owns the Stripe surface and can be the billing front for all of them).
- "Local market rate" / "industry benchmark" data is represented by curated sample benchmark tables
  in each MVP (same approach the flagship already uses), to be replaced with a real data feed later.
