# Resend Lead-Delivery Runbook

**Purpose:** Create a dependable first lead destination without prematurely choosing a CRM

**Version:** 1.0 | **Date:** 2026-08-29

## Preview

Create owner Resend account/project; use permitted test sender or verify a temporary/owned domain as required; add API key, FROM, and monitored notification email directly to Vercel Preview.

## Verify

Valid submission delivers; bad input 400; honeypot silently suppresses; rate limit works; provider failure returns safe failure; no form free text in analytics/logs; email contains only approved minimum lead information.

## CRM

CRM is optional for Preview when email delivery succeeds. Select CRM after real pipeline behavior shows required capabilities.

## Production

Use cleared White Oak domain, SPF/DKIM/DMARC as provider directs, approved privacy/retention, and monitored mailbox before public launch.
