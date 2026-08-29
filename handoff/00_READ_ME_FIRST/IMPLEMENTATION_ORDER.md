# Implementation Order

**Purpose:** Enforce the actual dependency chain

**Version:** 1.0 | **Date:** 2026-08-29

## Phase 1

Publish the existing Git repository privately using GitHub Desktop. Push `main` first, then `website-implementation`; preserve history and keep the latter checked out.

## Phase 2

Manually import the private repository into Vercel. Project name `white-oak-operations`; Root Directory `website`; Production branch `main`; no domain or live keys.

## Phase 3

Configure Preview-only services and variables: test Stripe, durable Redis-compatible store, Resend lead delivery. CRM may remain disabled if email delivery is functional.

## Phase 4

Deploy `website-implementation` as Preview. Run live HTTP, form, webhook, payment, accessibility, performance, metadata, noindex, and responsive QA.

## Phase 5

Run preliminary name clearance in parallel; then attorney review. Resolve entity, address, emails, domain, tax, contracts, and New York activity.

## Phase 6

After Preview and professional review, merge via reviewed pull request, configure Production variables/live objects, connect cleared domain through IONOS, deploy Production, smoke test, and preserve rollback.
