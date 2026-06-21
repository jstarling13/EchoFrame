"""
Stripe TEST-MODE setup for the EchoFrame checkout flow (dev only).
==================================================================
Creates test-mode Products + Prices + Payment Links via the Stripe API and
points each link's post-checkout redirect at the LOCAL backend's /upload page.
Then writes a local copy of the Clarity pricing page wired to the test links.

Nothing here touches live data: it refuses to run unless given an sk_test_ key.

Run:
    cd 01_Code/echoframe-backend
    STRIPE_TEST_SECRET_KEY=sk_test_xxx \
    BACKEND_URL=http://localhost:8000 \
    .venv/bin/python setup_stripe_test.py

Re-runs are idempotent (resources are tagged echoframe_test=1 and reused).
Prints the three payment-link URLs at the end.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import stripe

KEY = os.environ.get("STRIPE_TEST_SECRET_KEY", "").strip()
if not KEY.startswith("sk_test_"):
    sys.exit("Refusing to run: STRIPE_TEST_SECRET_KEY must be a sk_test_… key (got "
             f"{KEY[:8]!r}). This script only operates in Stripe TEST mode.")
stripe.api_key = KEY

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
REDIRECT = f"{BACKEND_URL}/upload?session_id={{CHECKOUT_SESSION_ID}}"

BASE_DIR = Path(__file__).resolve().parent
CLARITY_HTML = BASE_DIR.parent.parent / "site" / "intelligence" / "clarity.html"

# (name [must contain a _NAME_ROUTES needle so it routes to the engine],
#  unit_amount_cents, recurring?, the live buy.stripe.com link it replaces)
TIERS = [
    ("Monthly Clarity Report", 15000, True,  "https://buy.stripe.com/fZudRbezL9QB3jvdMbcwg00"),
    ("Competitor & Market Landscape Report", 29900, False, "https://buy.stripe.com/4gMeVf9fr4wh9HT4bBcwg02"),
    ("EchoFrame Business Audit", 49900, False, "https://buy.stripe.com/dRm28t1MZ6Ep1bn8rRcwg01"),
]

TAG = {"echoframe_test": "1"}


def _find_tagged_product(name: str):
    # Search is eventually-consistent; fall back to listing if it misses.
    for p in stripe.Product.search(query=f"metadata['echoframe_test']:'1' AND name:'{name}'").data:
        return p
    for p in stripe.Product.list(limit=100).auto_paging_iter():
        if p.get("name") == name and p.get("metadata", {}).get("echoframe_test") == "1":
            return p
    return None


def _ensure_product(name: str):
    existing = _find_tagged_product(name)
    if existing:
        return existing
    return stripe.Product.create(name=name, metadata=TAG)


def _ensure_price(product_id: str, amount: int, recurring: bool):
    for pr in stripe.Price.list(product=product_id, active=True, limit=100).auto_paging_iter():
        same_amount = pr.get("unit_amount") == amount
        same_kind = bool(pr.get("recurring")) == recurring
        if same_amount and same_kind:
            return pr
    kwargs = dict(product=product_id, unit_amount=amount, currency="usd", metadata=TAG)
    if recurring:
        kwargs["recurring"] = {"interval": "month"}
    return stripe.Price.create(**kwargs)


def _ensure_payment_link(price_id: str, name: str):
    # Reuse an active link for this price if one already points at our redirect.
    for pl in stripe.PaymentLink.list(limit=100).auto_paging_iter():
        if pl.get("metadata", {}).get("echoframe_test") != "1":
            continue
        if pl.get("metadata", {}).get("price_id") == price_id and pl.get("active"):
            return pl
    return stripe.PaymentLink.create(
        line_items=[{"price": price_id, "quantity": 1}],
        after_completion={"type": "redirect", "redirect": {"url": REDIRECT}},
        metadata={**TAG, "price_id": price_id, "name": name},
    )


def main() -> None:
    print(f"[setup] Stripe TEST mode. Redirect target: {REDIRECT}\n")
    results = []
    for name, amount, recurring, live_link in TIERS:
        prod = _ensure_product(name)
        price = _ensure_price(prod.id, amount, recurring)
        link = _ensure_payment_link(price.id, name)
        kind = "/mo" if recurring else " one-time"
        print(f"  {name:<40} ${amount/100:>7,.0f}{kind:<9}  {link.url}")
        results.append((name, live_link, link.url))

    # Write a local pricing page wired to the test links (original is untouched).
    if CLARITY_HTML.exists():
        html = CLARITY_HTML.read_text(encoding="utf-8")
        for _name, live_link, test_link in results:
            html = html.replace(live_link, test_link)
        banner = ('<div style="background:#0a274f;color:#fff;text-align:center;'
                  'padding:8px;font:600 13px system-ui">STRIPE TEST MODE — use card '
                  '4242 4242 4242 4242, any future date, any CVC. No real charge.</div>')
        html = re.sub(r"(<body[^>]*>)", r"\1" + banner, html, count=1)
        out = CLARITY_HTML.with_name("clarity.test.html")
        out.write_text(html, encoding="utf-8")
        print(f"\n[setup] Wrote test pricing page -> {out}")
        print(f"[setup] Serve site/ statically, then open /intelligence/clarity.test.html")
    else:
        print(f"\n[setup] WARN: {CLARITY_HTML} not found; skipped pricing-page rewrite.")
        print("[setup] You can still click the payment-link URLs above directly.")


if __name__ == "__main__":
    main()
