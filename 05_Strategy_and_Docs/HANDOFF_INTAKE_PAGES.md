# EchoFrame — Project Handoff (Post-Payment Intake Pages)

Paste this into a fresh Claude Code chat on the new machine. It contains
everything needed to keep working on the EchoFrame post-payment upload system.

## 1. What EchoFrame is
A studio that sells small-business "report" products. A customer buys a product
via Stripe, then lands on a Step-2 "secure upload" page where they drop a CSV.
That CSV is fed to the relevant report engine (which calls the Anthropic/Claude
API to write the narrative) and the finished report is emailed to them.

## 2. Where the code lives
Repo root on disk: `01_Code/echoframe-backend/` (inside the EchoFrame folder).
Two servers:
- `main.py`  — FastAPI. The REPORT INTAKE + webhook server. This is the one the
  intake pages talk to. Run: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- `server.js` — Express. Handles Stripe Checkout session creation only.

## 3. The intake-page system (what we built)
Goal: one post-payment "drop your file here" page per product, each telling the
customer exactly what data that product needs.

Key files:
- `intake_specs.py` — SINGLE SOURCE OF TRUTH for every single-CSV intake page.
  `INTAKE_SPECS` is a dict: slug -> page copy + form fields + requirements
  checklist + file labels. Reusable field helpers at top (F_BUSINESS, F_MONTH,
  F_CITY, F_ROLE, F_INDUSTRY, F_PERIOD).
- `templates/intake.html` — shared Jinja template all single-CSV pages render
  through. Reads `email` from the URL `?email=`, has a hidden `product` field so
  the backend knows which engine to run, POSTs to `/api/upload`.
- `templates/intake_revenue_suite.html` — SPECIAL 3-file page for Revenue Suite
  (it needs 3 CSVs at once). POSTs to `/api/upload-revenue-suite`.
- `products.py` — product registry. Maps slug -> engine adapter, defines tiers,
  and holds `STRIPE_PRODUCT_MAP` (live Stripe product IDs -> slug+tier).
- `main.py` — web layer. Routes by slug; no product-specific logic.
- `<product>_engine.py` — one per product; `generate_<product>_report(email, name, fields)`.
- `reports/intake_<slug>.html` — rendered previews of each page.

### Products with intake pages (all built)
Single-CSV (13): drive-pay, clarity, auto-ledger, rate-watch, shift-lens,
quote-revive, clear-ledger, permit-watch, bay-coach, call-catch, call-router,
rival-scan, crew-hire.
3-file: revenue-suite (Call Catch + Quote Revive + Clear Ledger).

Tiers: auto-ledger (starter/growth/pro), rate-watch (core/pro),
clear-ledger (starter/growth). Tier flows through as a hidden field; the
requirements checklist is the same across tiers.

### How CSV data is structured
Each engine reads a CSV whose business metadata lives in leading `_`-prefixed
rows (e.g. `_Business Name,...`, `_Owner Name,...`, `_Month,...`) followed by the
data table. See `demo_output/<product>_sample_input.csv` for the real shape of
every product. The customer name comes from the Stripe checkout (saved by the
webhook to `uploads/<safe_email>.json`), not the form.

## 4. How to add / change an intake page
1. Make sure `<product>_engine.py` exists with
   `generate_<product>_report(email, name, fields)` and is registered in
   `products.py` (adapter + PRODUCTS entry + STRIPE_PRODUCT_MAP).
2. Add one entry to `INTAKE_SPECS` in `intake_specs.py` (copy an existing one).
3. Render it: `python intake_specs.py <slug>`  (or `python intake_specs.py all`).
4. Output lands in `reports/intake_<slug>.html`.

For Revenue Suite there is no INTAKE_SPECS entry — it has its own template and
its own backend route (`/api/upload-revenue-suite`) that saves the 3 files as
`uploads/<safe_email>_callcatch.csv`, `_quoterevive.csv`, `_clearledger.csv`.

## 5. Backend routes in main.py
- GET  `/upload`                       — generic flagship upload page
- POST `/api/upload`                   — single-CSV intake; verifies Stripe
  session, validates CSV, dispatches the engine by `product` slug
- GET  `/upload/revenue-suite`         — serves the 3-file page
- POST `/api/upload-revenue-suite`     — accepts 3 CSVs, saves them, runs engine
- POST `/webhook/stripe`               — verifies signature, idempotent, on
  `checkout.session.completed` saves customer email+name for later attribution

## 6. Run it locally (new machine)
Prereqs: Python 3.12, Node (for server.js).
```
cd 01_Code/echoframe-backend
python -m venv .venv && source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env    # then fill in real values
uvicorn main:app --host 0.0.0.0 --port 4242
```
Required env vars (see `.env.example`): STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
ANTHROPIC_API_KEY, RESEND_API_KEY, CLIENT_URL, and the PRICE_ID_* vars.
NOTE: `main.py` refuses to start if STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
ANTHROPIC_API_KEY, or RESEND_API_KEY are missing.

Preview any intake page in a browser by opening `reports/intake_<slug>.html`
(append `?email=test@example.com` to populate the email).

## 7. Tests
```
python -m pytest tests/test_security.py -q -c /dev/null -o asyncio_mode=auto
```
(The `-c /dev/null -o asyncio_mode=auto` is a workaround — see Known Issues.)
Current status: 73 passing. 1 known pre-existing failure
(`test_path_traversal_in_filename_ignored`) — it patches
`main.generate_clarity_report`, which no longer exists after the move to the
products.py registry. It is a stale test, unrelated to the intake work.

## 8. Known issues / gotchas (IMPORTANT for the next agent)
- FILE-WRITE TRUNCATION: in the previous session, large single-shot file writes
  via the editor were silently truncated around ~4KB, corrupting files mid-line
  (it took out part of main.py's webhook handler once). When writing/replacing a
  large file, prefer writing it via a shell heredoc and ALWAYS verify afterward:
  `python -m py_compile <file>` and `wc -l <file>`. Avoid decorative multibyte
  box-drawing characters in source comments — a truncated multibyte char makes
  the file non-UTF-8 and unparseable. Stick to ASCII in comments.
- `pytest.ini` is itself truncated in the repo (ends mid-line at
  `asyncio_default_fi`). That's why tests are run with `-c /dev/null`. Worth
  fixing: restore it to `[pytest]\nasyncio_mode = auto`.
- Git: the repo's `.git` is a pointer (gitdir) to an external path, so in some
  environments git commands fail with "not a git repository." Don't rely on git
  for recovery; keep verifying writes.

## 9. Current state & what's left
DONE: all post-payment intake pages exist (13 single-CSV + Revenue Suite 3-file),
rendered, and the backend routes are in place and tested.
LEFT ("connect the source" future work): Call Catch, Call Router, Drive Pay,
Rival Scan, and Crew Hire are CSV-export drops today. The eventual vision is live
integrations (business phone line, shop-management system, job boards) instead of
a manual CSV export. That wiring is not built yet.
