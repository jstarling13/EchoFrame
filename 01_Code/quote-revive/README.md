# Quote Revive (MVP)

> *"You already did the work of quoting it. Quote Revive makes sure it actually closes."*
> — `echoframe-site/revenue/quoterevive.html`

Quote Revive watches open quotes, detects the ones going cold, and runs a **timed follow-up
sequence** automatically — escalating to a human handoff only when the sequence is exhausted.

The message **sender is injected** and defaults to an in-memory mock recorder, so running this
sends **nothing**. That's the documented seam where real SMS/email (e.g. the flagship's Resend, or
Twilio) plugs in.

## What it does
- Tracks each quote's status and how many follow-ups have been sent.
- Fires the next follow-up when enough days have passed since the last contact
  (schedule: day 2 → 4 → 7 → 14 after each contact; configurable).
- Composes context-aware messages (first nudge → softer mid → graceful final).
- After the last step, raises a **human-handoff** recommendation instead of more automation.
- Won't double-send in a day; stops entirely once a quote is accepted/declined.

## Run it

```powershell
cd 01_Code\quote-revive
pip install -r requirements.txt

python demo.py                         # simulate 22 days of follow-up (mock sender)
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8015   # HTTP API
```

### API
- `GET  /health`
- `POST /api/run-cycle` — process quotes for a given day (defaults to today):

```json
{
  "today": "2026-06-04",
  "quotes": [
    {"quote_id": "Q1", "customer_name": "Dana Reeves", "amount": 4800, "sent_date": "2026-06-02"}
  ]
}
```

Returns the messages the (mock) sender recorded, any handoffs, and the updated quote state
(`followups_sent`, `last_contact_date`) to persist back to your CRM.

## Assumptions / scope
- **Quotes come from the quoting tool / CRM**; that sync is the documented integration seam.
  This MVP is the "spot the cold ones + run the sequence + know when to hand off" core.
- **No real messages are sent** — `sender` is mock by default. Wire a real sender (Twilio SMS /
  Resend email) by passing a `Sender` callable; the flagship already owns a Resend integration.
- State (`followups_sent`, `last_contact_date`) is returned for the caller to persist; this MVP
  keeps no database. Run `run-cycle` once per day (cron) per the schedule.
- No auth/billing. Informational/automation aid only.
