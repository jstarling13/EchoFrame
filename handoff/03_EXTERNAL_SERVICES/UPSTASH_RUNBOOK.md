# Durable Store Runbook

**Purpose:** Enable production-like idempotency and rate limiting

**Version:** 1.0 | **Date:** 2026-08-29

## Provision

Create a dedicated Preview Redis-compatible REST database in the owner account. Use least privilege and a separate Production database later.

## Configure

Enter URL/token directly in Vercel Preview variables. Do not commit or share token. Redeploy.

## Verify

Contact rate-limit boundary and reset; store failure; Stripe duplicate event; process restart persistence; expiry; out-of-order event; logs contain no secrets or form free text.

## Gate

Production must fail closed for payment webhook idempotency when durable storage is missing. Preview should make missing configuration unmistakable.
