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
*(product MVP entries appended below as they are completed)*
