# Call Catch Engine

Missed-call auto-text backend for EchoFrame. Listens for inbound telephony
webhooks, detects missed/unanswered calls, and texts the caller back within ~60
seconds — then logs everything for the dashboard.

This folder is **fully isolated** from the EchoFrame web frontend (`app/`,
`components/`, `lib/`). It shares no files with the Next.js site.

## Stack
FastAPI · SQLAlchemy 2.0 · PostgreSQL (SQLite for local dev) · Twilio SDK ·
FastAPI BackgroundTasks for the delayed send.

## Quick start (local, mock SMS, SQLite)

```bash
cd call_catch_engine
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # default settings already work for local mock mode
# In .env set:  CALLCATCH_DATABASE_URL=sqlite:///./call_catch.db
#               CALLCATCH_USE_MOCK_SMS=true
#               CALLCATCH_SMS_SEND_DELAY_SECONDS=45

python seed.py                # creates a demo business + templates
uvicorn app.main:app --reload --port 8020
```

Open http://localhost:8020/docs for the interactive API.

## Simulate a missed call (Twilio-style)

```bash
curl -X POST http://localhost:8020/webhooks/twilio/voice-status \
  -d "CallSid=CA123" -d "From=+14045559876" -d "To=+14045550100" \
  -d "CallStatus=no-answer" -d "Direction=inbound"
```

Then read the dashboard (business id from the seed output, usually `1`):

```bash
curl http://localhost:8020/api/businesses/1/dashboard
curl http://localhost:8020/api/businesses/1/calls?missed_only=true
curl http://localhost:8020/api/businesses/1/sms
```

## How it works
1. **Webhook** (`routers/webhooks.py`) parses the Twilio form (or Telnyx JSON),
   routes to the tenant by the dialed number, and writes a `CallLog`.
2. If `CallStatus` is in `CALLCATCH_MISSED_STATUSES` (`no-answer,busy,failed`)
   and the business is active, it schedules `dispatch_missed_call_sms`.
3. **Dispatcher** (`services/sms_dispatcher.py`) waits the configured delay,
   picks the active template (after-hours vs business-hours), renders
   `{business}`/`{caller}`, sends via the telephony client, and writes an
   `SmsLog` with the delivery status.
4. **Dashboard** (`routers/dashboard.py`) serves call/SMS logs and a summary.

## Going to production
- **Database:** point `CALLCATCH_DATABASE_URL` at Postgres and manage schema
  with Alembic (remove the `init_db()` startup call).
- **SMS:** set `CALLCATCH_USE_MOCK_SMS=false` and provide
  `CALLCATCH_TWILIO_ACCOUNT_SID` / `CALLCATCH_TWILIO_AUTH_TOKEN`.
- **Security:** set `CALLCATCH_VALIDATE_TWILIO_SIGNATURE=true` and
  `CALLCATCH_PUBLIC_BASE_URL` so inbound webhooks are signature-verified.
- **Background work:** FastAPI `BackgroundTasks` holds the delayed send in-process,
  which is fine for moderate volume. For durability across restarts and high
  volume, swap `dispatch_missed_call_sms` for a Celery+Redis task — the function
  signature (`call_log_id`, `delay_seconds`) is already queue-friendly.

## Data model
- **BusinessProfile** — tenant; dialed number routes webhooks here.
- **MessageTemplate** — auto-text copy (`default` / `business_hours` / `after_hours`).
- **CallLog** — every inbound call attempt + whether it was missed/triggered a text.
- **SmsLog** — every outbound auto-text + delivery status.
