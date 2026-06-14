#!/usr/bin/env node
/**
 * test-purchases.js
 * -----------------------------------------------------------------------------
 * Runs a REAL test purchase against every active product/price in your Stripe
 * SANDBOX (test mode) and prints a pass/fail table. Nothing here touches live.
 *
 *   - Recurring prices  -> creates a customer, attaches the test card, creates a
 *                          subscription, and checks the first invoice is paid.
 *                          The subscription is canceled again right after.
 *   - One-time prices   -> creates and confirms a PaymentIntent for the price
 *                          amount and checks it succeeds.
 *
 * Uses Stripe's built-in test payment method `pm_card_visa` (the 4242 card).
 *
 * -----------------------------------------------------------------------------
 * RUN (needs only your sandbox/test key):
 *   $env:STRIPE_TEST_KEY="sk_test_...from the sandbox..."   # PowerShell
 *   node test-purchases.js
 *
 *   # macOS/Linux bash:  STRIPE_TEST_KEY=sk_test_... node test-purchases.js
 * -----------------------------------------------------------------------------
 */

const Stripe = require("stripe");

const TEST_KEY = process.env.STRIPE_TEST_KEY;
if (!TEST_KEY || !TEST_KEY.startsWith("sk_test")) {
  console.error("✖ STRIPE_TEST_KEY must be set to your sandbox/test secret key (sk_test_...).");
  console.error("  This script NEVER runs against live. It refuses anything that isn't sk_test_.");
  process.exit(1);
}
const stripe = new Stripe(TEST_KEY);

const money = (amt, cur) => (amt == null ? "—" : `$${(amt / 100).toFixed(2)} ${cur.toUpperCase()}`);
const pad = (s, n) => String(s).padEnd(n).slice(0, n);

async function testRecurring(price, productName) {
  const customer = await stripe.customers.create({
    email: "test+echoframe@example.com",
    name: "Test Buyer",
    metadata: { purpose: "echoframe-test-purchase" },
  });
  const pm = await stripe.paymentMethods.attach("pm_card_visa", { customer: customer.id });
  await stripe.customers.update(customer.id, {
    invoice_settings: { default_payment_method: pm.id },
  });

  const sub = await stripe.subscriptions.create({
    customer: customer.id,
    items: [{ price: price.id }],
    default_payment_method: pm.id,
    expand: ["latest_invoice"],
    metadata: { purpose: "echoframe-test-purchase" },
  });

  const invoiceStatus = sub.latest_invoice ? sub.latest_invoice.status : "none";
  const ok = (sub.status === "active" || sub.status === "trialing") &&
             (invoiceStatus === "paid" || sub.status === "trialing");

  // clean up so the sandbox doesn't keep billing this test sub
  try { await stripe.subscriptions.cancel(sub.id); } catch (_) {}

  return {
    ok,
    detail: `sub ${sub.status}, invoice ${invoiceStatus}`,
  };
}

async function testOneTime(price) {
  const pi = await stripe.paymentIntents.create({
    amount: price.unit_amount,
    currency: price.currency,
    payment_method: "pm_card_visa",
    confirm: true,
    automatic_payment_methods: { enabled: true, allow_redirects: "never" },
    metadata: { purpose: "echoframe-test-purchase" },
  });
  return { ok: pi.status === "succeeded", detail: `payment_intent ${pi.status}` };
}

(async () => {
  const acct = await stripe.accounts.retrieve().catch(() => null);
  console.log(`Running TEST purchases in sandbox${acct ? ` ${acct.id}` : ""}\n`);

  const rows = [];
  for await (const price of stripe.prices.list({ active: true, limit: 100, expand: ["data.product"] })) {
    const product = price.product && typeof price.product === "object" ? price.product : null;
    const name = product ? product.name : (typeof price.product === "string" ? price.product : "?");
    if (product && product.active === false) continue;

    const isRecurring = price.type === "recurring";
    const kind = isRecurring ? `${money(price.unit_amount, price.currency)}/${price.recurring.interval}` : `${money(price.unit_amount, price.currency)} one-time`;

    let result;
    try {
      result = isRecurring ? await testRecurring(price, name) : await testOneTime(price);
    } catch (e) {
      result = { ok: false, detail: e.message };
    }
    rows.push({ name, kind, ok: result.ok, detail: result.detail });
    console.log(`${result.ok ? "✓" : "✖"} ${pad(name, 34)} ${pad(kind, 18)} ${result.detail}`);
  }

  const passed = rows.filter((r) => r.ok).length;
  const failed = rows.length - passed;
  console.log("\n=== Summary ===");
  console.log(`Tested: ${rows.length}   Passed: ${passed}   Failed: ${failed}`);
  if (failed) {
    console.log("\nFailures:");
    for (const r of rows.filter((x) => !x.ok)) console.log(`  ✖ ${r.name} (${r.kind}) — ${r.detail}`);
  } else {
    console.log("All products charged successfully on the test card.");
  }
  console.log("\nNote: these are sandbox charges only — no real money moved.");
})().catch((e) => {
  console.error("\n✖ Failed:", e && e.message ? e.message : e);
  process.exit(1);
});
