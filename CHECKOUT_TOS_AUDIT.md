# Checkout — Terms-of-Service Consent Audit

**Result: ✅ PASS — all 20 Payment Links require Terms-of-Service consent at checkout.**

**Verified:** resolved 2026-06-24 via the Stripe API (live mode), reading
`consent_collection.terms_of_service` on every Payment Link — all 20 now `required`.
Account: `EchoFrame` (`acct_1Ta0p0RoVBvZMFsw`).

**History:** the 2026-06-21 audit found 0/20 links gating on ToS (toggle OFF on all).
Fix: account ToS URL set to `https://echoframe.net/terms.html` (Settings → Public
details), then **"Require customers to accept your Terms of Service" turned ON for each
link in the dashboard** (Advanced options). The edits were in place — same plink ids,
**same `buy.stripe.com` URLs** — so the links already wired into the site are now
ToS-gated and **no site change or redeploy was required**.

**Why it matters:** the arbitration clause and liability cap in `terms.html` are now
assented to by the customer at the moment of purchase, on every product.

---

## Findings — all 20 links (current state)

`ToS required` = Stripe `consent_collection.terms_of_service`. `required` = PASS.

| # | Product | ToS required? | plink id | Link |
|--|--|:--:|--|--|
| 1  | Auto Ledger (Pro)     | ✅ required | `plink_1Teje3RoVBvZMFswGeorV1LZ` | https://buy.stripe.com/5kQ8wR77je6RaLX8rRcwg05 |
| 2  | Auto Ledger (Growth)  | ✅ required | `plink_1TejdhRoVBvZMFswm2zwyXIE` | https://buy.stripe.com/6oU7sNfDP6Ep3jv5fFcwg04 |
| 3  | Auto Ledger (Starter) | ✅ required | `plink_1Tejd2RoVBvZMFswUS8Nrggh` | https://buy.stripe.com/8x228tajvd2Ng6h9vVcwg03 |
| 4  | Business Audit        | ✅ required | `plink_1TaeC9RoVBvZMFsw7AVFLhHE` | https://buy.stripe.com/dRm28t1MZ6Ep1bn8rRcwg01 |
| 5  | Clarity               | ✅ required | `plink_1TaeC9RoVBvZMFswlYO9gknc` | https://buy.stripe.com/fZudRbezL9QB3jvdMbcwg00 |
| 6  | Competitor Landscape  | ✅ required | `plink_1TaeC9RoVBvZMFswJIIRweEM` | https://buy.stripe.com/4gMeVf9fr4wh9HT4bBcwg02 |
| 7  | Rate Watch (Pro)      | ✅ required | `plink_1TejuNRoVBvZMFswoQ8d4qSi` | https://buy.stripe.com/3cI7sN9fr9QB9HTfUjcwg07 |
| 8  | Rate Watch (Core)     | ✅ required | `plink_1TejtLRoVBvZMFswfYwlwn1P` | https://buy.stripe.com/fZueVf3V76Ep7zL23tcwg06 |
| 9  | Rival Scan            | ✅ required | `plink_1TejwnRoVBvZMFswsqqsb7uk` | https://buy.stripe.com/14AaEZ8bn8MxdY95fFcwg08 |
| 10 | Shift Lens            | ✅ required | `plink_1TelDjRoVBvZMFswWF9IXqbG` | https://buy.stripe.com/4gMfZj1MZ0g19HT6jJcwg09 |
| 11 | Bay Coach             | ✅ required | `plink_1TelSWRoVBvZMFswR2kT97nm` | https://buy.stripe.com/14A8wR4Zb6EpdY95fFcwg0h |
| 12 | Permit Watch          | ✅ required | `plink_1TelNfRoVBvZMFswVhpOZakf` | https://buy.stripe.com/5kQaEZdvHe6R2frbE3cwg0f |
| 13 | Drive Pay             | ✅ required | `plink_1TelUfRoVBvZMFswDVJkBXZ0` | https://buy.stripe.com/6oU00lezLd2N8DP5fFcwg0i |
| 14 | Crew Hire             | ✅ required | `plink_1TelQ1RoVBvZMFswArigi12e` | https://buy.stripe.com/cNi00l77j2o96vH0Zpcwg0g |
| 15 | Call Router           | ✅ required | `plink_1TelMRRoVBvZMFswQhfKq2e8` | https://buy.stripe.com/cNi5kFezLaUF6vH7nNcwg0e |
| 16 | Clear Ledger (Growth) | ✅ required | `plink_1TelKERoVBvZMFswmMmOAaly` | https://buy.stripe.com/4gM28tajv6Ep6vH0Zpcwg0d |
| 17 | Clear Ledger (Starter)| ✅ required | `plink_1TelJqRoVBvZMFswF4h2UxFZ` | https://buy.stripe.com/14A3cxcrDgeZ6vHgYncwg0c |
| 18 | Quote Revive          | ✅ required | `plink_1TelHYRoVBvZMFswzHhSMPdQ` | https://buy.stripe.com/8x29AV9fraUF8DPazZcwg0b |
| 19 | Call Catch            | ✅ required | `plink_1TelFcRoVBvZMFsweiunYzBw` | https://buy.stripe.com/eVqbJ34Zb2o9f2d7nNcwg0a |
| 20 | Revenue Suite         | ✅ required | `plink_1TkT7YRoVBvZMFswGeAEuYRq` | https://buy.stripe.com/9B67sNgHT7It5rDbE3cwg0j |

**Note (side effect to review):** while enabling ToS, **automatic tax was also turned ON**
for **Business Audit** and **Competitor Landscape** (both were tax-OFF before). Clarity
remains tax-OFF. Not a defect — just confirm you intended to start collecting sales tax on
those two one-time products. To re-verify the whole set any time:
list Payment Links and confirm every `consent_collection.terms_of_service` == `required`.

---

## Related: bleach in the Railway build (Job 2) — ✅ PASS

Closed conclusively (no email render needed):
- `bleach>=6.0` in `01_Code/echoframe-backend/requirements.txt:17`; only `Procfile` +
  `requirements.txt` present, so Nixpacks installs `requirements.txt` directly.
- Service is live serving the latest deploy → the build's `pip install` succeeded.
- Templates render the AI narrative through `| clean` (58 template lines; 15 engines wire
  `env.filters["clean"] = html_safe.clean`); **no** narrative uses raw `| safe`. So real
  bold/dollar formatting renders; if bleach were ever absent it degrades to escaping, so
  generation never breaks.
