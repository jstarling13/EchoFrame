# IONOS DNS connection plan

**Status:** not started. This implementation session has no IONOS
credentials, API access, or MCP tool available — none of the steps below
have been executed. They are written for the owner (or a future session
with IONOS access) to follow.

## Before touching DNS

1. Log into the IONOS control panel and **export/screenshot the complete
   current DNS zone** for the domain, especially:
   - `MX` records (mail routing)
   - `TXT` records for `SPF` (`v=spf1 ...`)
   - `TXT`/`CNAME` records for `DKIM` (often `selector._domainkey`)
   - `TXT` record for `DMARC` (`_dmarc`)
   - Any other `A`/`CNAME`/`TXT` records serving existing services
2. Save that export somewhere durable (e.g. `operations/` in this repo, or
   the owner's password manager/docs) before changing anything. This is
   the rollback reference.

## Connecting the domain (record-level, not nameserver migration)

3. In Vercel, add the production domain to the project. Vercel will
   display the **exact** apex `A` record and `www` `CNAME`/verification
   values for this specific project — use those exact values, not generic
   example IPs from any documentation (including this one).
4. In IONOS, add/update only the apex `A` record and `www` `CNAME` (or
   equivalent) to the values Vercel displayed. Leave every mail-related
   record (`MX`, `SPF`, `DKIM`, `DMARC`) untouched.
5. Do **not** migrate nameservers to Vercel unless the owner explicitly
   approves it and every existing record (especially mail) has been
   recreated on the new nameservers first. Record-level connection is the
   default and preserves IONOS as the DNS operator.

## After the change

6. Verify, once DNS has propagated:
   - Apex domain loads the site over HTTPS with a valid certificate.
   - `www` redirects to the canonical host (or vice versa, per the final
     redirect decision).
   - Outbound/inbound email still works (send a real test message).
   - SSL certificate issuance completed in Vercel without errors.
7. Record the before/after zone export and verification results as
   evidence (see `14_CLAUDE_IMPLEMENTATION/TEST_PLAN.md` "Evidence").

## Explicit owner decision still needed

The permanent domain name itself has not been chosen — it depends on the
trademark/domain screening for the permanent company name (see
`strategy/OPEN_QUESTIONS.md`). This plan is domain-agnostic and applies
once that decision is made.
