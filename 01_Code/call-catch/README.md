# Call Catch (MVP)

> *"The second you miss a call, a text goes out. The lead stays warm until you can follow up."*
> — `echoframe-site/revenue/missedcall.html`

Call Catch turns a missed call into an instant auto-text, picks the right message for
business-hours vs after-hours/weekend, dedupes repeat callers, and keeps a missed-call log.

The SMS sender is **injected** (mock recorder by default) — running this sends **nothing**.
The telephony webhook (Twilio etc. firing on a missed call) is the documented integration seam.

## What it does
- `handle_missed_call(...)` composes and sends the text **synchronously** (the "under-60-second"
  promise), then logs the event.
- Business-hours vs after-hours/weekend template selection (configurable hours + templates).
- Dedupes repeat calls from the same number (logged, not re-texted) — avoids spamming a caller.
- Missed-call log dashboard: totals, texts sent, after-hours count, unique callers.

## Run it

```powershell
cd 01_Code\call-catch
pip install -r requirements.txt

python demo.py                         # offline sample of incoming missed calls
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8017   # HTTP API
```

### API (simulates the telephony webhook)
- `GET  /health`
- `POST /webhook/missed-call` — `{"caller_number": "+17065550101", "occurred_at": "2026-06-02T10:30:00"}`
- `GET  /api/dashboard` — missed-call log + counts

## Assumptions / scope
- **The missed-call signal comes from a telephony provider webhook** (Twilio/RingCentral/etc.).
  That integration is the documented seam; this MVP is the "compose the right text instantly +
  log + dedupe" core.
- **No real texts sent** — pass a real `Sender` (Twilio SMS) to go live.
- State (log, seen numbers) is in-process for the MVP; production persists per tenant.
- Default hours are Mon–Fri 8–5, weekends closed; pass `business_hours`/`templates` to customize.
- No auth/billing.
