# EchoFrame Clarity Report — Local Setup & Run Guide

The flagship backend turns a small-business financial CSV into a branded, narrated
4-page **Monthly Financial Clarity Report** (`.docx`) and emails it. This guide gets it
running locally, runs the tests, and produces a real report **with no external calls**.

> For Stripe webhook forwarding specifically, see `README_TESTING.md`.
> For security details, see `SECURITY.md`.

---

## 1. Prerequisites

- **Python 3.12** (tested on 3.12.3)
- pip

## 2. Install dependencies

From this folder (`01_Code/echoframe-backend/`):

```powershell
# (recommended) create a local virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # PowerShell
# source .venv/bin/activate         # macOS/Linux

pip install -r requirements.txt
```

All math/document libraries (pandas, python-docx, matplotlib) and the API SDKs
(stripe, anthropic, resend) are pinned in `requirements.txt`.

## 3. Configure environment

Copy the schema and fill in real values (never commit `.env` — it is gitignored):

```powershell
Copy-Item .env.example .env
```

`main.py` requires these four at startup or it refuses to boot:

| Variable | Used for |
|---|---|
| `STRIPE_SECRET_KEY` | verifying the paid Checkout session before accepting an upload |
| `STRIPE_WEBHOOK_SECRET` | validating Stripe webhook signatures |
| `ANTHROPIC_API_KEY` | Claude writes the report prose (numbers come from pandas, never the LLM) |
| `RESEND_API_KEY` | emailing the finished `.docx` |

Optional: `EMAIL_FROM` (defaults to `EchoFrame <reports@echoframe.co>`),
`CLIENT_URL`, `PORT`, and the `PRICE_ID_*` values used by the Node Checkout front (`server.js`).

## 4. Run the offline demo (no keys, no network, no email)  ← start here

This is the fastest way to see a real report. It mocks Anthropic, Resend, and Stripe
entirely and writes a finished `.docx` to `demo_output/`:

```powershell
python demo_local.py
```

Expected tail:

```
[EchoFrame] Report saved -> EchoFrame_reliable_heating_air_<timestamp>.docx
[demo] _send_report_email mocked — NO email sent.
[demo] SUCCESS — report written: ...\demo_output\EchoFrame_reliable_heating_air_<timestamp>.docx  (~144 KB)
```

Open the `.docx` in `demo_output/` to view the 4-page report. No API keys are needed
because every external service is mocked.

## 5. Run the test suite

```powershell
python -m pytest -q
```

Expected: **83 passed**. The tests set their own placeholder env vars (see
`tests/conftest.py`), mock all external services, and assert that the security controls
(payment gate, upload validation, prompt-injection sanitization, rate limiting, webhook
signature checks) all hold.

## 6. Run the live API server (needs real/test keys in `.env`)

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

Endpoints:
- `GET  /upload` — drop-zone UI (HTML)
- `POST /api/upload` — CSV intake; verifies Stripe session, validates, kicks off report
- `POST /webhook/stripe` — Stripe webhook (records customer name/email on checkout completion)

---

## CSV format

Rows beginning with `_` are metadata; all other rows are financial line items.
Columns: `Category, Current, Prior` (Prior optional).

```csv
_Business Name,Reliable Heating & Air,
_Owner Name,Shane,
_Industry,HVAC,
_Location,Columbus GA,
_Employees,8,
_Month,May 2026,
_Context,Spring tune-up season; hired a second seasonal tech.,
Revenue,52000,44000
Labor Cost,18720,14080
Parts & Materials,9360,8800
Marketing,780,880
Utilities,624,528
Misc,1040,880
```

`Revenue` is required and must be > 0. Industry drives the benchmark table
(90+ industries built in; a generic table is used for unknown industries).

---

## How it fits together

```
CSV ──► pandas (ALL math: variances vs benchmark, leak ranking, health score)
          │
          ├──► Claude haiku via tool_use  (prose ONLY — never numbers)
          │
          └──► python-docx (4-page branded report)
                    │
                    ├──► saved to reports/   (_save_report)
                    └──► emailed via Resend   (_send_report_email)
```

Separation of concerns is strict and intentional: the LLM never produces a number,
and all client-supplied text is sanitized before it reaches the prompt.

---

## Maintenance note (2026-06-02)

`engine.py` was found **truncated** (it ended mid-function, so the module would not
import and every test errored at collection). Three things were restored/added:
1. completed the cut-off `_set_cell_bg` shading helper;
2. reconstructed `_save_report` and `_send_report_email` (lost past the truncation
   point), matching the naming of previously generated reports;
3. added `tests/test_engine_pipeline.py` so the truncation cannot silently recur.

See `OVERNIGHT_LOG.md` for the full account.
