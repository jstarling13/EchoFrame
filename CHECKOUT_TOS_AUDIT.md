# Checkout — Terms-of-Service Consent Audit

**Generated:** 2026-06-21 · **Against commit:** `0c7e997` · **Site source of truth:**
`grep -rho "https://buy.stripe.com/[A-Za-z0-9]*" site/ | sort -u`

**Why this matters:** the ToS consent gate at checkout is what makes the arbitration
clause and liability cap in `terms.html` *enforceable* — the customer assents at the
moment of purchase. A Payment Link that reaches "Pay" with no ToS consent = the legal
terms aren't bound to that sale.

**How to verify each link (dashboard — authoritative):**
Stripe → **Payment Links** → open the link → **After payment → Options** → confirm
**"Require customers to accept your Terms of Service"** is **ON** and points at
`https://echoframe.net/terms.html`. Tick both boxes only when confirmed.

> Products with multiple links (Auto Ledger ×3, Rate Watch ×2, Clear Ledger ×2) are
> separate tier/variant pages — **each has its own toggle**. Don't skip the duplicates.

PASS for the whole audit = all 20 rows have both boxes checked.

---

## The 20 live Payment Links

| # | Product | ToS required ON | → terms.html | Link |
|--|--|:--:|:--:|--|
| 1  | Auto Ledger (tier 1)    | ☐ | ☐ | https://buy.stripe.com/5kQ8wR77je6RaLX8rRcwg05 |
| 2  | Auto Ledger (tier 2)    | ☐ | ☐ | https://buy.stripe.com/6oU7sNfDP6Ep3jv5fFcwg04 |
| 3  | Auto Ledger (tier 3)    | ☐ | ☐ | https://buy.stripe.com/8x228tajvd2Ng6h9vVcwg03 |
| 4  | Business Audit          | ☐ | ☐ | https://buy.stripe.com/dRm28t1MZ6Ep1bn8rRcwg01 |
| 5  | Clarity                 | ☐ | ☐ | https://buy.stripe.com/fZudRbezL9QB3jvdMbcwg00 |
| 6  | Competitor Landscape    | ☐ | ☐ | https://buy.stripe.com/4gMeVf9fr4wh9HT4bBcwg02 |
| 7  | Rate Watch (a)          | ☐ | ☐ | https://buy.stripe.com/3cI7sN9fr9QB9HTfUjcwg07 |
| 8  | Rate Watch (b)          | ☐ | ☐ | https://buy.stripe.com/fZueVf3V76Ep7zL23tcwg06 |
| 9  | Rival Scan              | ☐ | ☐ | https://buy.stripe.com/14AaEZ8bn8MxdY95fFcwg08 |
| 10 | Shift Lens              | ☐ | ☐ | https://buy.stripe.com/4gMfZj1MZ0g19HT6jJcwg09 |
| 11 | Bay Coach               | ☐ | ☐ | https://buy.stripe.com/14A8wR4Zb6EpdY95fFcwg0h |
| 12 | Permit Watch            | ☐ | ☐ | https://buy.stripe.com/5kQaEZdvHe6R2frbE3cwg0f |
| 13 | Drive Pay               | ☐ | ☐ | https://buy.stripe.com/6oU00lezLd2N8DP5fFcwg0i |
| 14 | Crew Hire               | ☐ | ☐ | https://buy.stripe.com/cNi00l77j2o96vH0Zpcwg0g |
| 15 | Call Router             | ☐ | ☐ | https://buy.stripe.com/cNi5kFezLaUF6vH7nNcwg0e |
| 16 | Clear Ledger (a)        | ☐ | ☐ | https://buy.stripe.com/14A3cxcrDgeZ6vHgYncwg0c |
| 17 | Clear Ledger (b)        | ☐ | ☐ | https://buy.stripe.com/4gM28tajv6Ep6vH0Zpcwg0d |
| 18 | Quote Revive            | ☐ | ☐ | https://buy.stripe.com/8x29AV9fraUF8DPazZcwg0b |
| 19 | Call Catch              | ☐ | ☐ | https://buy.stripe.com/eVqbJ34Zb2o9f2d7nNcwg0a |
| 20 | Revenue Suite           | ☐ | ☐ | https://buy.stripe.com/9B67sNgHT7It5rDbE3cwg0j |

---

## Re-run the enumeration any time

If you add or change a Payment Link on the site, regenerate the canonical list and
diff it against this table so no new link slips through unaudited:

```sh
grep -rho "https://buy.stripe.com/[A-Za-z0-9]*" site/ | sort -u
```

Map each link back to its product page with:

```sh
for u in $(grep -rho "https://buy.stripe.com/[A-Za-z0-9]*" site/ | sort -u); do
  echo "$u"; grep -rl "$u" site/ | sed 's#^#    #'
done
```

---

## Related: bleach in the Railway build (Job 2)

- **Static — PASS:** `bleach>=6.0` in `01_Code/echoframe-backend/requirements.txt:17`;
  only `Procfile` + `requirements.txt` present (no nixpacks/Pipfile/poetry/pyproject),
  so Nixpacks installs `requirements.txt` directly — nothing shadows it.
- **Runtime — corroborated:** the service is live serving `0c7e997`, so the build's
  `pip install` succeeded (bleach resolved). `html_safe.clean()` degrades to escaping
  if bleach were ever absent, so generation never breaks regardless.
- **Authoritative render check (do once):**
  `GET /api/review/selftest-real?key=<YOUR_SELFTEST_KEY>` on the Railway host, then open
  the `[REVIEW]` email and confirm the attached Auto Ledger report shows **real bold +
  green dollar figures** (PASS) and not literal `<b>` / `&lt;b&gt;` (FAIL). Equivalent:
  grep the Railway deploy log for `bleach`.
