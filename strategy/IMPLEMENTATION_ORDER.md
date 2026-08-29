# Implementation Order

**Purpose:** Sequence local implementation with explicit gates

**Version:** 1.0 | **Date:** 2026-08-28

## Phase 0: inspect

Inventory any existing repository, brand assets, domain, Stripe account structure, analytics, and forms. Preserve good work. Create a branch before edits.

## Phase 1: decide

Resolve business name, legal entity, domain, contact routes, service-area language, tax treatment, governing law, and privacy contact. Replace only documented decision tokens.

## Phase 2: commercial foundation

Review legal drafts with counsel — selected per the factors in
`OPEN_QUESTIONS.md` "Professional review" (entity formation state,
principal place of business, where services are performed, where clients
are located, regulated industries/data — not assumed to be New York just
because initial clients are there); approve offers, prices, payment
terms, travel terms, and security boundaries. Configure CRM and client
folder structure.

## Phase 3: website

Integrate website starter into the selected framework. Add validated copy, forms, consent logging, analytics, accessibility, security headers, and test coverage.

## Phase 4: Stripe

Create products and prices in test mode from the catalog. Implement invoices/payment links and webhook idempotency. Reconcile all objects by metadata.

## Phase 5: deploy

Connect Git, configure Vercel Preview and Production variables, deploy preview, run acceptance tests, then configure IONOS DNS using values shown by Vercel.

## Phase 6: launch operations

Load templates, rehearse discovery and delivery, run one discounted-but-paid design-partner engagement, capture baseline/actual value, and request a case study only after results are verified.
