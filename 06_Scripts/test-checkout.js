#!/usr/bin/env node
/**
 * test-checkout.js — create a TEST-mode subscription checkout for the most
 * expensive recurring product (Auto Ledger — Pro, $299/mo) on a Stripe Test
 * Clock, so we can later fast-forward a month for the renewal.
 *
 * Pay on the printed URL with card 4242 4242 4242 4242 (any future expiry,
 * any CVC, any ZIP). On success Stripe redirects to the local upload page.
 *
 * RUN:  STRIPE_TEST_KEY=sk_test_... node test-checkout.js
 */
const Stripe = require("stripe");
const fs = require("fs");

const key = process.env.STRIPE_TEST_KEY;
if (!key || !key.startsWith("sk_test")) {
  console.error("✖ Set STRIPE_TEST_KEY to your sk_test_ key first.");
  process.exit(1);
}
const s = new Stripe(key);

const PRICE = "price_1ThvBwRoVBvZMFsweD1nnTzE";      // Auto Ledger — Pro, $299/mo
const CUSTOMER_EMAIL = "jacobstarling4313+customer@gmail.com";

(async () => {
  const clock = await s.testHelpers.testClocks.create({
    frozen_time: Math.floor(Date.now() / 1000),
    name: "EchoFrame E2E " + new Date().toISOString().slice(0, 16),
  });
  const cust = await s.customers.create({
    email: CUSTOMER_EMAIL,
    name: "Test Customer — Auto Ledger Pro",
    test_clock: clock.id,
  });
  const session = await s.checkout.sessions.create({
    mode: "subscription",
    customer: cust.id,
    line_items: [{ price: PRICE, quantity: 1 }],
    success_url: "http://localhost:8000/upload?session_id={CHECKOUT_SESSION_ID}",
    cancel_url: "http://localhost:8000/?canceled=1",
  });

  const ctx = {
    clock: clock.id, customer: cust.id, email: CUSTOMER_EMAIL,
    session: session.id, url: session.url, price: PRICE,
  };
  fs.writeFileSync("/tmp/ef_test_ctx.json", JSON.stringify(ctx, null, 2));

  console.log("\n=== EchoFrame test checkout ready =====================");
  console.log("Product:   Auto Ledger — Pro  ($299/mo)");
  console.log("Customer:  " + CUSTOMER_EMAIL);
  console.log("TestClock: " + clock.id);
  console.log("Customer:  " + cust.id);
  console.log("\n>>> OPEN THIS URL AND PAY with 4242 4242 4242 4242 (any future date / CVC / ZIP):\n");
  console.log(session.url);
  console.log("\n(saved context to /tmp/ef_test_ctx.json for the renewal step)");
  console.log("=======================================================\n");
})().catch((e) => { console.error("✖ ERROR:", e.message); process.exit(1); });
