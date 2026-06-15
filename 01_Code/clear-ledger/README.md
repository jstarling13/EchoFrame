# Clear Ledger (MVP)

> *"You did the work. Clear Ledger makes sure you actually get paid for it — without you
> having to ask twice."* — `echoframe-site/revenue/clearledger.html`

Clear Ledger runs an invoice **dunning sequence** from first friendly nudge to final notice,
keeps an **AR aging dashboard**, and raises a **human-handoff** alert when an invoice stays
overdue after the full sequence.

The message sender is **injected** (mock recorder by default) — running this sends **nothing**.

## What it does
- Fires reminders at absolute days-past-due milestones (1 / 7 / 14 / 30; configurable).
- Relationship-preserving message tone that escalates: gentle reminder → check-in → final notice.
- **AR aging summary**: open invoice count, total outstanding, buckets (current / 1-30 / 31-60 / 60+).
- Raises a human-handoff alert once reminders are exhausted; no double-send/day; stops when paid.

## Run it

```powershell
cd 01_Code\clear-ledger
pip install -r requirements.txt

python demo.py                         # offline cycle + AR summary (mock sender)
python -m pytest -q                    # tests (all pass, no network)
uvicorn api:app --reload --port 8016   # HTTP API
```

### API
- `GET  /health`
- `POST /api/run-cycle` — send due reminders + return AR summary (defaults to today)
- `POST /api/ar-summary` — AR aging only

```json
{
  "today": "2026-06-02",
  "invoices": [
    {"invoice_id": "INV-201", "customer_name": "Dana Reeves", "amount": 1800, "due_date": "2026-05-31"}
  ]
}
```

Returns the (mock) messages sent, handoffs, AR aging, and updated `reminders_sent` to persist.

## Assumptions / scope
- **Invoices come from the invoicing tool** (QuickBooks/Stripe/etc.); that sync is the documented
  integration seam. This MVP is the dunning + AR-aging + handoff core.
- **No real messages sent** — pass a real `Sender` (Resend email / Twilio SMS) to go live; the
  flagship already owns a Resend integration.
- State (`reminders_sent`) is returned for the caller to persist; no DB. Run once/day via cron.
- No auth/billing. Informational/automation aid only.
