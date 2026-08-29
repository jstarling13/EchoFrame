# Stripe Test-Mode Runbook

**Purpose:** Create and verify test payment objects without exposing keys

**Version:** 1.0 | **Date:** 2026-08-29

## Owner action

Enter test key locally or run the documented sync command yourself from `website/`. Do not paste key into chat, Git, screenshots, or shell history where avoidable.

## Amounts

O1 $2,500; O2 deposit $3,750; O3 deposit $7,200; O4 deposit $13,500; O5 $2,500/month. Later O2-O4 milestones use private invoices, not public reusable Checkout.

## Webhook

After Preview URL exists, create test endpoint `<preview-url>/api/stripe/webhook`; subscribe only to documented events; set signing secret directly in Vercel Preview; redeploy.

## Tests

Successful/failed/3DS/async payment; invalid signature; duplicate and out-of-order event; restart/durable idempotency; refund; dispute; subscription lifecycle; missing/wrong metadata; test/live separation; project reconciliation.

## Authority

Signed MSA/SOW and internal project record control scope. Stripe controls payment status. Payment never starts work automatically.
