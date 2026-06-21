# Checkout — Terms-of-Service Consent Audit

**Result: ❌ FAIL — 0 of 20 Payment Links gate on Terms of Service.**

**Verified:** 2026-06-21 via the Stripe API (live mode), reading
`consent_collection.terms_of_service` on every Payment Link — authoritative, not a
visual check. Account: `EchoFrame` (`acct_1Ta0p0RoVBvZMFsw`).

**Why this matters:** the ToS consent gate at checkout is what binds the arbitration
clause and liability cap in `terms.html` to the sale — the customer assents at the
moment of purchase. With the toggle OFF, **no customer has agreed to the Terms at
purchase on any product.** The ToS checkbox on `site/get-a-sample.html` covers only the
free-sample form, NOT the paid Stripe checkout. This is the highest-stakes item in the
whole QA cycle and it is currently failing on 100% of links.

---

## Findings — all 20 links

`ToS required` = Stripe `consent_collection.terms_of_service`. `none` = toggle OFF (FAIL).

| # | Product | ToS required? | plink id | Link |
|--|--|:--:|--|--|
| 1  | Auto Ledger (tier 1)  | ❌ none | `plink_1Teje3RoVBvZMFswGeorV1LZ` | https://buy.stripe.com/5kQ8wR77je6RaLX8rRcwg05 |
| 2  | Auto Ledger (tier 2)  | ❌ none | `plink_1TejdhRoVBvZMFswm2zwyXIE` | https://buy.stripe.com/6oU7sNfDP6Ep3jv5fFcwg04 |
| 3  | Auto Ledger (tier 3)  | ❌ none | `plink_1Tejd2RoVBvZMFswUS8Nrggh` | https://buy.stripe.com/8x228tajvd2Ng6h9vVcwg03 |
| 4  | Business Audit        | ❌ none | `plink_1TaeC9RoVBvZMFsw7AVFLhHE` | https://buy.stripe.com/dRm28t1MZ6Ep1bn8rRcwg01 |
| 5  | Clarity               | ❌ none | `plink_1TaeC9RoVBvZMFswlYO9gknc` | https://buy.stripe.com/fZudRbezL9QB3jvdMbcwg00 |
| 6  | Competitor Landscape  | ❌ none | `plink_1TaeC9RoVBvZMFswJIIRweEM` | https://buy.stripe.com/4gMeVf9fr4wh9HT4bBcwg02 |
| 7  | Rate Watch (a)        | ❌ none | `plink_1TejuNRoVBvZMFswoQ8d4qSi` | https://buy.stripe.com/3cI7sN9fr9QB9HTfUjcwg07 |
| 8  | Rate Watch (b)        | ❌ none | `plink_1TejtLRoVBvZMFswfYwlwn1P` | https://buy.stripe.com/fZueVf3V76Ep7zL23tcwg06 |
| 9  | Rival Scan            | ❌ none | `plink_1TejwnRoVBvZMFswsqqsb7uk` | https://buy.stripe.com/14AaEZ8bn8MxdY95fFcwg08 |
| 10 | Shift Lens            | ❌ none | `plink_1TelDjRoVBvZMFswWF9IXqbG` | https://buy.stripe.com/4gMfZj1MZ0g19HT6jJcwg09 |
| 11 | Bay Coach             | ❌ none | `plink_1TelSWRoVBvZMFswR2kT97nm` | https://buy.stripe.com/14A8wR4Zb6EpdY95fFcwg0h |
| 12 | Permit Watch          | ❌ none | `plink_1TelNfRoVBvZMFswVhpOZakf` | https://buy.stripe.com/5kQaEZdvHe6R2frbE3cwg0f |
| 13 | Drive Pay             | ❌ none | `plink_1TelUfRoVBvZMFswDVJkBXZ0` | https://buy.stripe.com/6oU00lezLd2N8DP5fFcwg0i |
| 14 | Crew Hire             | ❌ none | `plink_1TelQ1RoVBvZMFswArigi12e` | https://buy.stripe.com/cNi00l77j2o96vH0Zpcwg0g |
| 15 | Call Router           | ❌ none | `plink_1TelMRRoVBvZMFswQhfKq2e8` | https://buy.stripe.com/cNi5kFezLaUF6vH7nNcwg0e |
| 16 | Clear Ledger (a)      | ❌ none | `plink_1TelJqRoVBvZMFswF4h2UxFZ` | https://buy.stripe.com/14A3cxcrDgeZ6vHgYncwg0c |
| 17 | Clear Ledger (b)      | ❌ none | `plink_1TelKERoVBvZMFswmMmOAaly` | https://buy.stripe.com/4gM28tajv6Ep6vH0Zpcwg0d |
| 18 | Quote Revive          | ❌ none | `plink_1TelHYRoVBvZMFswzHhSMPdQ` | https://buy.stripe.com/8x29AV9fraUF8DPazZcwg0b |
| 19 | Call Catch            | ❌ none | `plink_1TelFcRoVBvZMFsweiunYzBw` | https://buy.stripe.com/eVqbJ34Zb2o9f2d7nNcwg0a |
| 20 | Revenue Suite         | ❌ none | `plink_1TkT7YRoVBvZMFswGeAEuYRq` | https://buy.stripe.com/9B67sNgHT7It5rDbE3cwg0j |

Also `custom_text.terms_of_service_acceptance` is `null` on all 20 (no custom consent
copy either).

---

## Remediation

Each link needs `consent_collection[terms_of_service] = required`. Two paths:

**A. Dashboard (per link):** Stripe → Payment Links → open link → After payment →
Options → turn ON "Require customers to accept your Terms of Service".

**B. API (all 20 at once):** `POST /v1/payment_links/{id}` with
`consent_collection[terms_of_service]=required` for each plink id above.

**Prerequisite for BOTH:** Stripe requires a **Terms of Service URL** set on the account
first — Settings → Public details → "Terms of service" → `https://echoframe.net/terms.html`.
Until that public ToS URL is set, Stripe rejects turning the per-link toggle on. The URL
shown to customers comes from this account setting (it is not per-link).

**Re-verify after fixing** (re-run this read):
- API: list payment links, confirm every `consent_collection.terms_of_service` == `required`.
- Enumeration unchanged-check: `grep -rho "https://buy.stripe.com/[A-Za-z0-9]*" site/ | sort -u`

---

## Related: bleach in the Railway build (Job 2) — ✅ PASS

Closed conclusively (no email render needed):
- `bleach>=6.0` in `01_Code/echoframe-backend/requirements.txt:17`; only `Procfile` +
  `requirements.txt` present, so Nixpacks installs `requirements.txt` directly.
- Service is live serving `0c7e997` → the build's `pip install` succeeded (bleach resolved).
- Templates render the AI narrative through `| clean` (58 template lines; 15 engines wire
  `env.filters["clean"] = html_safe.clean`); **no** narrative uses raw `| safe`. So the
  chain `narrative → | clean → html_safe.clean → bleach → Markup` yields real bold/dollar
  formatting. `html_safe.clean()` degrades to escaping if bleach were ever absent, so
  generation never breaks regardless.
