# EchoFrame — Checkout & Fulfillment (how every product is actually sold)

**Status:** authoritative reference · **Last updated:** 2026-06-20
**Why this exists:** checkout works two different ways and most of it isn't in the
repo. This is the single source of truth so nothing falls through the cracks
(addresses §D of the QA audit).

---

## The big picture — pay first, fulfill later

EchoFrame's purchase and report delivery are **two separate steps**, joined only
by the customer's email:

1. **Checkout** (Stripe) → customer pays. The webhook saves *only* their email +
   name. **No report is generated here.**
2. **Upload** (Step-2 intake page) → customer returns, uploads their CSV, and the
   matching engine generates + delivers the report (held for your review via
   `review_gate`).

> ⚠️ **Known gap:** a customer who pays and never returns to upload gets nothing
> automatic. There is no "you paid but haven't uploaded" reminder. If you see a
> `checkout.session.completed` with no follow-up upload, chase it manually.

---

## How checkout actually works

**The live site sells every product through a per-product Stripe Payment Link**
embedded directly in that product's page — the "Subscribe →" / "Get the … →"
buttons link straight to `buy.stripe.com/…`. These links live in **Stripe**, not
in the repo. (`server.js` *also* exposes a programmatic Checkout-Session endpoint
for three products via `PRICE_ID_*` env vars, but the live pages don't use it —
treat it as an alternate/legacy path, not the source of truth.)

**Per Payment Link, in the Stripe Dashboard, you must:**

- ✅ Set the price/recurrence.
- ✅ **Enable "Require customers to accept your Terms of Service"** → point it at
  `https://echoframe.net/terms.html`. (Can't be set via API on Payment Links —
  it's a per-link toggle. Miss it = ROSCA/CAN-SPAM exposure.)
- ✅ Set success/cancel URLs to the **canonical domain** (`echoframe.net`).

### Product → Payment Link map (verified 2026-06-20 from the live site pages)

The "Link" column is the `buy.stripe.com/…` suffix actually wired on the page.
Price is from the engine source docstring; the **authoritative live price is
whatever the Payment Link is set to** in Stripe.

| Section | Product | Page | Payment Link(s) | Price |
|---|---|---|---|---|
| Intelligence | Clarity (Monthly) | `intelligence/clarity.html` | `…wg00` | $150/mo |
| Intelligence | Business Audit | `intelligence/business-audit.html` | `…wg01` | $499 one-time |
| Intelligence | Competitor Landscape | `intelligence/competitor-landscape.html` | `…wg02` | $299 one-time |
| Intelligence | Auto Ledger | `intelligence/auto-ledger.html` | `…wg03` / `…wg04` / `…wg05` | tiered |
| Intelligence | Rate Watch | `intelligence/rate-watch.html` | `…wg06` / `…wg07` | tiered |
| Intelligence | Rival Scan | `intelligence/rival-scan.html` | `…wg08` | $129/mo |
| Intelligence | Shift Lens | `intelligence/shift-lens.html` | `…wg09` | $149/mo |
| Revenue | Call Catch | `revenue/call-catch.html` | `…wg0a` | from $79/mo |
| Revenue | Quote Revive | `revenue/quote-revive.html` | `…wg0b` | $99/mo |
| Revenue | Clear Ledger | `revenue/clear-ledger.html` | `…wg0c` / `…wg0d` | $49 / $99/mo |
| Revenue | **Revenue Suite** (bundle) | `revenue/revenue-suite.html` | **none yet — TODO** | $199/mo |
| Ops | Call Router | `ops/call-router.html` | `…wg0e` | $179 |
| Ops | Permit Watch | `ops/permit-watch.html` | `…wg0f` | $89 |
| Ops | Crew Hire | `ops/crew-hire.html` | `…wg0g` | $149 |
| Ops | Bay Coach | `ops/bay-coach.html` | `…wg0h` | $129 |
| Ops | Drive Pay | `ops/drive-pay.html` | `…wg0i` | $79 |

> ✅ **Done:** Business Audit (`…wg01`) and Competitor (`…wg02`) new pages are wired
> to their existing Payment Links; the Clarity page was trimmed to Clarity-only
> (the one-time products now live solely on their own pages).
>
> 🔧 **The one remaining checkout gap:** **Revenue Suite** has no Payment Link — it's
> the new bundle page. Create a `$199/mo` Payment Link in Stripe (ToS toggle ON,
> canonical URLs) and paste it over the `TODO(jacob)` markers in
> `revenue/revenue-suite.html`.

---

## The webhook (`main.py` → `POST /webhook/stripe`)

Signature-verified (300s tolerance), size-capped (1 MB), idempotent (each event
id processed once via the durable store or in-memory fallback).

- **`checkout.session.completed`** → saves buyer `email` + `name` only (so the
  upload page can attribute the report later). **Does not generate anything.**
- **`invoice.payment_succeeded`** → monthly renewal fulfillment (`_handle_invoice_paid`);
  deliberately skips the first `subscription_create` invoice (already covered by
  checkout) to avoid double-sending.

---

## Fulfillment (the Step-2 upload → report)

1. Customer lands on the per-product intake/upload page and uploads their CSV.
   The page carries a `product` field that selects the engine.
2. `registry.py` maps that product slug → the engine's `generate(email, name, fields)`.
3. The engine parses (robust `csv_utils`), runs the **data-quality gate**
   (`data_quality`), computes, renders, and sends.
4. Three safety nets wrap delivery (see the engines' module docstrings):
   `email_failsafe` (delivery), `fulfillment_guard` (nothing produced → calm
   note + owner alert, now with a **specific** reason when we have one — B-5),
   and `review_gate` (every report held for your "Approve & send").

---

## Domain & config — pick one and keep it

- **Canonical domain: `echoframe.net`.** (`echoframe.co` was a mistake; the site
  canonical tags were corrected to `.net` — see the QA remediation.)
- `.env` `CLIENT_URL` must be the production URL in prod (it defaults to
  `http://localhost:3000` for dev — success/cancel URLs break if not overridden).
- ToS link everywhere: `https://echoframe.net/terms.html`.
- **Report sender email** is `@echoframe.co` in the engines' `EMAIL_FROM` default
  — that's a *separate* concern from the website domain; don't "fix" it to match
  unless you've moved the sending domain in Resend.

---

## Test-mode checkout (run before touching live)

From `01_Code/echoframe-backend` (the script refuses any non-`sk_test_` key):

```bash
STRIPE_TEST_SECRET_KEY=sk_test_… BACKEND_URL=http://localhost:8000 python setup_stripe_test.py
```

It creates test products/prices/payment links and points redirects at your local
backend. Complete a purchase with card `4242 4242 4242 4242`.

---

## Checklist when adding / changing a product

- [ ] Site page exists under `site/<section>/<slug>.html`, linked in `nav.js`,
      `sitemap.xml`, and the section `index.html` (0 dangling links).
- [ ] Checkout wired: create a per-product **Stripe Payment Link** (ToS toggle ON +
      canonical `echoframe.net` URLs) and paste it into the page's buy button(s).
      Add it to the Product → Payment Link map above.
- [ ] Engine registered in `registry.py` with the product slug.
- [ ] The intake/upload page passes the correct `product` slug.
- [ ] Verified end-to-end in **test mode** before going live.
