# EchoFrame — Local Webhook Testing Guide

## Prerequisites

Install the Stripe CLI (Windows):
```powershell
# Via scoop
scoop install stripe

# Or download the .exe directly from:
# https://github.com/stripe/stripe-cli/releases/latest
```

Log in to your Stripe account:
```bash
stripe login
```

Install Python dependencies:
```bash
pip install fastapi uvicorn stripe python-dotenv pandas
```

---

## Step 1 — Start the local server

Open a terminal in `C:\Users\jacob\OneDrive\EchoFrame\echoframe-backend` and run:

```bash
uvicorn stripe_webhook:app --reload --host 0.0.0.0 --port 8000 --env-file .env
```

`--env-file .env` tells uvicorn to load the variables directly at boot, which bypasses any `python-dotenv` path issues entirely.

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

---

## Step 2 — Forward Stripe webhooks to localhost

Open a **second terminal** and run:

```bash
stripe listen --forward-to localhost:8000/webhook/stripe
```

Stripe will print a webhook signing secret that looks like:
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

**Copy that `whsec_...` value** and paste it into `.env` (in this same folder):
```
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxx
```

Then restart the server (Step 1) so it picks up the new value.

---

## Step 3 — Fire a test event

In a **third terminal**, trigger a mock `checkout.session.completed` event:

```bash
stripe trigger checkout.session.completed
```

### What you should see

**Server terminal:**
```
[EchoFrame] Payment confirmed — someone@example.com | $0.00
[EchoFrame] Report written → echoframe-backend/reports/report_someone_at_example_com_20260522_....txt
```

**`stripe listen` terminal:**
```
2026-05-22 --> checkout.session.completed [evt_...]
2026-05-22 <-- [200] POST http://localhost:8000/webhook/stripe
```

A `.txt` report file will appear in `echoframe-backend/reports/` (created automatically on first run).

---

## Useful test commands

| Command | What it does |
|---|---|
| `stripe trigger checkout.session.completed` | Fire a completed checkout event |
| `stripe events list` | See recent events in your Stripe account |
| `stripe logs tail` | Stream live API request logs |
| `stripe listen --print-json --forward-to localhost:8000/webhook/stripe` | Same as above but prints the full JSON payload |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `KeyError: 'STRIPE_SECRET_KEY'` | You're not running uvicorn from `echoframe-backend/`, or forgot `--env-file .env`. Run the exact command in Step 1. |
| `400 Invalid Stripe signature` | The `STRIPE_WEBHOOK_SECRET` in `.env` doesn't match the one printed by `stripe listen`. Re-copy it and restart the server. |
| `500` error on the server | Check the uvicorn terminal for the Python traceback. Most likely a missing dependency (`pip install ...`). |
| No report file created | The `reports/` folder is created automatically — check the uvicorn terminal for a Python traceback from `engine.py`. |
