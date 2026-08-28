# Decision Log

**Purpose:** Record decisions that drive cross-file consistency

**Version:** 1.0 | **Date:** 2026-08-28

## Approved v1 architecture

- **O1**: Workflow Opportunity Diagnostic at $2,500; deposit $2,500; 10 business days.
- **O2**: Workflow Build Sprint at $7,500; deposit $3,750; 4 weeks.
- **O3**: AI Operations Transformation at $18,000; deposit $7,200; 8-10 weeks.
- **O4**: Enterprise AI Operations Program at $45,000; deposit $13,500; 16-20 weeks.
- **O5**: Workflow Assurance & Enablement at $2,500; deposit $2,500; Monthly; 3-month initial term.

## Positioning

Category: AI Operations Enablement. Promise: convert repeatable knowledge work into governed, tested workflows that the client can operate and improve. Differentiator: consulting + implementation + role-based training + ownership transfer.

## Go-to-market

Referral-first New York entry. Prioritize accounting, commercial real estate/property management, construction services, recruiting/staffing, and established professional services. Delay highly regulated autonomous decision use cases.

## Payment rules

Deposits are non-refundable once reserved work or discovery begins, subject to contract and applicable law. Change requests require written approval. Late invoices pause work after notice. Travel outside the agreed local radius is pre-approved and passed through at cost unless fixed in the SOW.

## Technical

Use Stripe-hosted payment surfaces initially. Store no card data. Use server-side webhook verification and idempotent event processing. Preserve IONOS email-related DNS records when connecting Vercel.
