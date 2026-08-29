# Test Plan

**Purpose:** Require evidence before deployment

**Version:** 1.0 | **Date:** 2026-08-28

## Static

Dependency install lockfile; lint; typecheck; unit; configuration/schema parse; no secrets; license/vulnerability review.

## Website

Every route/status; keyboard/focus; screen-reader landmarks/labels/errors; contrast; 320-1440px; reduced motion; forms validation/abuse/error/success; email/CRM; consent; analytics data minimization; metadata/canonical/sitemap/robots/structured data; broken links; 404.

## Stripe

Test Checkout/Payment Link/Invoice/Subscription; success/failure/3DS/async; signed/invalid webhook; duplicate/out-of-order; refund/dispute; cancellation; metadata; no card storage; test/live isolation; reconciliation.

## Deployment

Production build; Preview smoke; env scope; security headers; logs; observability; custom domain; SSL; apex/www; email DNS; rollback.

## Business consistency

Exact O1-O5 names, prices, deposits, schedules, scope language across site, Stripe, proposals, legal drafts, and workbooks.

## Evidence

Command, date, commit SHA, environment, result, artifact/screenshot/log reference, tester, exception/approval.
