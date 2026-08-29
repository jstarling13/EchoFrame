# IONOS Domain Runbook

**Purpose:** Connect a cleared domain without breaking email

**Version:** 1.0 | **Date:** 2026-08-29

## Before

Domain selected/cleared; add to Vercel; export entire IONOS zone; identify MX, SPF, DKIM, DMARC, verification, and other service records; capture current website state.

## Change

Use exact A/CNAME/verification values Vercel displays at the time. Prefer record-level connection. Do not migrate nameservers unless owner explicitly approves and every record is recreated.

## Verify

Apex, www redirect, SSL, email send/receive, SPF/DKIM/DMARC, forms, Stripe return URLs, sitemap/canonical, monitoring. Allow propagation; retain rollback values.

## Rollback

Restore previous web records if site/SSL fails; never remove mail records as website troubleshooting.
