# Production Promotion Gate

**Purpose:** Prevent a technically healthy Preview from becoming a premature business launch

**Version:** 1.0 | **Date:** 2026-08-29

## Required

Preview approved; name/domain risk accepted after clearance; entity and public facts; counsel-approved legal documents; production email; Production durable store; live Stripe objects/webhook; privacy/analytics; insurance/accounting; IONOS plan; rollback; owner authorization.

## Git

Reviewed PR from `website-implementation` to `main`; CI green; diff reviewed; no secrets; branch protection as appropriate; release tag/commit recorded.

## Deployment

Production variables entered directly; deploy main; verify domain/SSL/email/payment/forms/logs; one controlled live payment/refund if approved; monitoring and rollback ready.

## Stop

Any unresolved critical security/payment/legal/name/data issue; draft banners not intentionally resolved; missing contact destination; live/test mix; broken email DNS; no rollback.
