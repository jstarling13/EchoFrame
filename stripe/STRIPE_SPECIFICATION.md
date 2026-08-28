# Stripe Specification

**Purpose:** Implement payments without inventing local state

**Version:** 1.0 | **Date:** 2026-08-28

## Object strategy

Create one Product per O1-O5 and Prices matching product_catalog. Use Stripe Invoices for bespoke/milestone engagements; hosted Payment Links or Checkout for standard deposits/prepaid services; Subscription for O5. Do not encode every milestone as a public reusable price unless operationally useful.

## Metadata

On Customer, Checkout Session/Payment Link where supported, PaymentIntent, Invoice, Subscription: client_id, project_id, offer_code, sow_id, environment, source, owner. Never store sensitive workflow content in metadata.

## Checkout

Collect business name, buyer name/email, billing address as required, terms/SOW acknowledgment reference, and promotion codes only if approved. Use hosted Stripe surfaces. Success page verifies session server-side and shows no confidential details. Payment success does not replace signed contract.

## Invoices

Create from signed SOW; line items identify offer/milestone/project; ACH/card based on account decision; due dates match contract; memo includes project/SOW ID; reconcile payout, fee, refund, and receivable status.

## Webhooks

Minimum: checkout.session.completed, checkout.session.async_payment_succeeded/failed, payment_intent.succeeded/payment_failed, invoice.paid/payment_failed/overdue/voided, customer.subscription.created/updated/deleted, charge.refunded, charge.dispute.created/closed. Verify signature using raw body; store event ID; idempotent handler; acknowledge quickly; retry-safe; log result without secrets/PII.

## Entitlement/status

Contract and internal project record remain authoritative for service scope. Stripe is authoritative for payment status. A webhook updates payment state and creates an operations task; it must not automatically begin risky work.

## Cancellation/refunds

O5 cancel at period end after initial term unless contract says otherwise. No prorating assumption. Refunds require policy/contract approval and reason; use original charge; update project accounting; preserve audit trail. Disputes trigger evidence preservation and owner review.

## Test cases

Successful/failed/3DS/async payment; duplicate/out-of-order webhook; invalid signature; invoice overdue; subscription cancel/renew/fail; partial/full refund; dispute; wrong metadata; test/live key separation; reconciliation to project ID.
