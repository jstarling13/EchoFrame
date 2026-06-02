# EchoFrame — Overnight Engineering Log

Autonomous overnight run. Newest entries at the bottom. All work is on branch
**`overnight/products-2026-06-02`** (never on `main`). Nothing pushed.

---

## 2026-06-02 — Session start, audit, and flagship rescue

### Environment notes
- `01_Code/echoframe-backend` and `01_Code/echoframe-site` are **OneDrive reparse points**, not
  git symlinks. Git tracks the real files normally (confirmed via `git ls-files` / `git status`).
- Python 3.12.3; all backend dependencies already installed globally (imports verified).
- **Pre-existing uncommitted changes** to 18 `echoframe-site` HTML files + `nav.js` + a new
  `Open EchoFrame Site.bat` were present in the working tree at session start. These are **NOT
  mine** — they predate this run. I have **left them untouched and unstaged**. I am committing
  only files I created or changed, so the owner's in-progress site edits are preserved as-is.

### AUDIT (STATUS.md)
- Read all 12 marketing product pages (the specs) + the full `echoframe-backend` source/tests.
- Wrote `01_Code/STATUS.md`: per-product table (code exists?, state, MVP definition), grouped the
  12 concept products by buildability, and recorded assumptions.

### CRITICAL FINDING — flagship was broken (truncated `engine.py`)
The starting brief said Clarity Report "works." In fact the working copy of `engine.py` was
**truncated mid-function** — the file ended at an unterminated string literal inside
`_set_cell_bg`. Consequences:
- `engine.py` would not import → `main.py` would not import → **all 75 tests errored at
  collection** (`SyntaxError: unterminated string literal`).
- The committed `HEAD` copy is truncated at the **identical** spot, so this was committed broken.
- The engine had clearly worked before (dozens of generated `.docx` reports dated 2026-05-31 in
  `reports/`), so the truncation happened *after* those were produced. No intact copy exists in
  git history (`engine.py` has a single commit, also truncated).

Static analysis (`ast`) showed the truncation also deleted two module-level functions that are
called by `generate_clarity_report` but were defined past the cut point:
`_save_report` and `_send_report_email`.

### FIXES (flagship hardening)
1. **Completed `_set_cell_bg`** — the standard python-docx cell-shading helper
   (`w:val=clear`, `w:color=auto`, `w:fill=<hex>`, append to `tcPr`).
2. **Reconstructed `_save_report`** — writes the `.docx` to `REPORTS_DIR` and returns the path.
   Filename convention reverse-engineered from existing reports:
   `EchoFrame_<business-slug>_<YYYYMMDD>_<HHMMSS>.docx`, where the slug lowercases the business
   name and maps non-alphanumerics to `_` (verified: "Reliable Heating & Air" →
   `reliable_heating_air`, "Lumière Salon & Spa" → `lumi_re_salon_spa`, matching on-disk files).
3. **Reconstructed `_send_report_email`** — emails the `.docx` via Resend as a base64 attachment,
   with a plain-English body + disclaimer; `from` defaults to `EchoFrame <reports@echoframe.co>`
   and is overridable via `EMAIL_FROM`. (Never invoked for real in tests/demo — always mocked.)
4. **`pytest.ini`** — set `asyncio_default_fixture_loop_scope = function` to silence the
   pytest-asyncio deprecation warning.
5. **`demo_local.py`** (new) — fully-offline demo: mocks Anthropic + Resend, writes a sample CSV,
   and produces a real 4-page `.docx` in `demo_output/`. No keys, no network, no email.
6. **`tests/test_engine_pipeline.py`** (new) — 8 tests covering `_report_slug`, `_save_report`
   naming, `_send_report_email` (Resend mocked), and the full pipeline end-to-end (narrative +
   email mocked). Guards against the truncation regression recurring.
7. **`SETUP.md`** (new) — local setup, env schema, demo, tests, server run, CSV format.
8. **`.gitignore`** — added `demo_output/`, `.venv/`, `.pytest_cache/`.

### How to run / verify (flagship)
```powershell
cd 01_Code\echoframe-backend
pip install -r requirements.txt
python demo_local.py        # offline: writes a real .docx to demo_output\, no network
python -m pytest -q         # 83 passed
```

### Test results
- Before fix: **collection error** (0 runnable).
- After fix: **75 passed** (existing) → **83 passed** (after adding `test_engine_pipeline.py`).
- Offline demo: SUCCESS — `EchoFrame_reliable_heating_air_<ts>.docx` (~144 KB), email mocked,
  nothing left the machine.

### Decisions / assumptions
- `_send_report_email`'s exact Resend payload and `from` address could not be recovered (lost with
  the truncation). Reconstructed to the documented Resend Python SDK contract with an overridable
  `EMAIL_FROM`. This path is never exercised live in tests/demo, so correctness of the live send
  is **owner-verifiable** but not risky to the test/demo flow.
- Did not "fix" pre-existing library `FutureWarning`s in the docx builder
  (`tbl_el.find(qn(...)) or _el(...)` truthiness) — currently functional; out of scope and would
  touch a lot of working code. Noted here as a future cleanup.

### Known items for the owner (non-blocking)
- In-memory Stripe webhook idempotency store → move to Redis for multi-process deploys
  (already flagged as a `PRODUCTION NOTE` in `main.py`).
- Reports/uploads write to local disk → object storage at scale.
- `README_TESTING.md` references the old module name `stripe_webhook:app` and an old path; the
  current entry point is `main:app`. Left as-is (didn't want to rewrite owner's doc); `SETUP.md`
  is the authoritative current guide.

---

## 2026-06-02 — Product MVP #1: Rate Watch (`rate-watch/`)  ✅ done

**Page:** `intelligence/oryn.html` · **Core promise:** benchmark vendor spend vs market, flag
overpays, alert before renewals.

**Built:** pure-Python engine (`engine.py`) + FastAPI wrapper (`api.py`) + offline `demo.py` +
13 tests + README + requirements. No external calls anywhere.
- Compares each vendor to a curated `(low, typical, high)` market band per category.
- Classifies over/within/under/no_benchmark, computes overpay $/mo + %, ranks largest gaps,
  totals monthly & annual savings.
- Flags renewals due within a window (default 30 days) — the page's renewal-alert promise.

**Run:** `cd 01_Code\rate-watch && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8011` · tests: `python -m pytest -q`.

**Test results:** 13 passed. Demo: reviewed 7 vendors, found 4 overpayers, $670/mo
($8,040/yr) potential savings, 2 renewals flagged.

**Assumptions:** market bands are a curated sample table (documented seam for a real local-market
feed, same pattern as the flagship's industry benchmarks); national bands stand in for "local";
no auth/billing/persistence (flagship Stripe surface fronts it); informational only.

---

## 2026-06-02 — Product MVP #2: Shift Lens (`shift-lens/`)  ✅ done

**Page:** `intelligence/strata.html` · **Core promise:** per-shift labor-vs-revenue P&L, flag
underperformers, schedule recommendations.

**Built:** `engine.py` (per-shift P&L + classification + weekly aggregation) + `api.py` (FastAPI)
+ `demo.py` + 15 tests + README + requirements. No external calls.
- Per shift: labor %, contribution (revenue−labor), status (healthy/watch/underperforming/
  no_revenue), and a concrete recommendation.
- Labor accepted as direct `labor_cost` or `labor_hours × avg_wage`.
- Weekly roll-up: totals, overall labor %, ranked underperformers, best/worst shift.
- Configurable `target_labor_pct` (default 30%).

**Run:** `cd 01_Code\shift-lens && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8012` · tests: `python -m pytest -q`.

**Test results:** 15 passed. Demo: 6 shifts, flagged a money-losing Wed Lunch (140% labor) and a
65%-labor Tue Lunch; identified Sat Dinner as best.

**Assumptions:** input is already-joined shift rows (POS↔scheduling join is the upstream seam);
"contribution" = revenue − labor only (shift-level lever, not full profit); default target is a
restaurant norm; no auth/billing/persistence; informational only.

---

## 2026-06-02 — Product MVP #3: Permit Watch (`permit-watch/`)  ✅ done

**Page:** `ops/permitwatch.html` · **Core promise:** one dashboard of licenses/permits with
30-day expiry alerts + per-vehicle tracking.

**Built:** `engine.py` (expiry status + dashboard + per-entity grouping + alert digest) + `api.py`
(FastAPI) + `demo.py` + 13 tests + README + requirements. No external calls.
- Per item: days-to-expiry + status (expired / critical ≤7d / due_soon ≤window / upcoming / ok).
- Dashboard sorted most-urgent-first, status counts, grouped by entity (per-vehicle).
- `render_alert_digest`: inbox-ready 30-day heads-up.
- Replaced a `⚠` glyph with ASCII after it crashed the Windows cp1252 console (portability fix).

**Run:** `cd 01_Code\permit-watch && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8013` · tests: `python -m pytest -q`.

**Test results:** 13 passed. Demo: flagged 1 expired (Van 12 registration), 1 critical (Truck 3
DOT inspection, 5 days), 1 due (business license, 22 days), grouped across 4 entities.

**Assumptions:** items are user-maintained (matches the page's "enter your fleet" step; no DMV
integration); inbox delivery is a thin daily-cron wrapper over `render_alert_digest` (reuses
flagship Resend); document storage/history deferred; no auth/billing; informational only.

---

## 2026-06-02 — Product MVP #4: Bay Coach (`bay-coach/`)  ✅ done

**Page:** `ops/baysignal.html` · **Core promise:** right service recommendation at write-up from
vehicle history + mileage.

**Built:** `engine.py` (maintenance-interval rules engine) + `api.py` (FastAPI) + `demo.py` +
13 tests + README + requirements. No external calls.
- Compares miles-since-last against a standard interval table (oil, tires, brakes, fluids, plugs).
- Per service: status (overdue/due/upcoming/ok), miles since/until, advisor-readable reason.
- Never-recorded service treated as due with a "confirm with customer" note; ranked most-urgent.

**Run:** `cd 01_Code\bay-coach && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8014` · tests: `python -m pytest -q`.

**Test results:** 13 passed. Demo (2019 Camry @ 68,400 mi): flagged 7 overdue, 2 upcoming.

**Assumptions:** vehicle+history come from the shop management system (documented integration
seam); standard passenger-vehicle interval table (per-make tables drop in without engine change);
mileage-based, not an inspection (write-up text says so); month-only intervals surfaced for manual
review; no auth/billing; informational only.

---

## 2026-06-02 — Product MVP #5: Quote Revive (`quote-revive/`)  ✅ done

**Page:** `revenue/quoterevive.html` · **Core promise:** auto follow-up sequence on ghosted
quotes, escalate to a human when exhausted.

**Built:** `engine.py` (sequence engine, **injected sender** defaulting to a mock recorder) +
`api.py` (FastAPI) + `demo.py` (16-day simulation) + 11 tests + README + requirements.
- Fires follow-ups at absolute milestones (days since sent: 2/4/7/14; configurable).
- Context-aware messages (first nudge → softer → graceful final), no double-send/day, stops on
  accepted/declined, raises a human-handoff after the last step.
- **No real messages sent** — sender is injected; mock by default. Real SMS/email is the seam.

**Run:** `cd 01_Code\quote-revive && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8015` · tests: `python -m pytest -q`.

**Test results:** 11 passed. Demo: 4 follow-ups across 14 days then a day-15 handoff, mock sender
recorded 4 messages (nothing sent).

**Note/decision:** first design used "days since last contact" (stacking) which pushed step 4 to
day 27; switched to absolute "days since sent" milestones for a predictable cadence.

**Assumptions:** quotes come from the quoting tool/CRM (integration seam); state is returned for
the caller to persist (no DB); run once/day via cron; no auth/billing.

---

## 2026-06-02 — Product MVP #6: Clear Ledger (`clear-ledger/`)  ✅ done

**Page:** `revenue/clearledger.html` · **Core promise:** invoice dunning sequence + AR dashboard +
human-handoff alerts.

**Built:** `engine.py` (dunning sequence + AR aging, **injected mock sender**) + `api.py` (FastAPI)
+ `demo.py` + 13 tests + README + requirements. No real messages sent.
- Reminders at days-past-due milestones (1/7/14/30; configurable), escalating tone
  (gentle → check-in → final notice), human-handoff after the sequence.
- AR aging summary: open count, total outstanding, buckets (current/1-30/31-60/60+).

**Run:** `cd 01_Code\clear-ledger && pip install -r requirements.txt && python demo.py` ·
API: `uvicorn api:app --reload --port 8016` · tests: `python -m pytest -q`.

**Test results:** 13 passed (fixed two test-expectation bugs: final notice fires at the 30-day
milestone; a May-1→Jun-2 invoice is 32 days = 31-60 bucket — engine was correct). Demo: 2 reminders
sent, 1 handoff, AR aging $7,550 outstanding across buckets.

**Assumptions:** invoices come from the invoicing tool (integration seam); no real sends (inject a
real Sender to go live, reuse flagship Resend); state returned for caller to persist; no DB/auth.

---
*(product MVP entries appended below as they are completed)*
