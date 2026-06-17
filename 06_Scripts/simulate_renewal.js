#!/usr/bin/env node
/**
 * simulate_renewal.js — fast-forward the Stripe test clock one month so the
 * subscription bills again, then deliver that renewal invoice to the local
 * server as a properly-signed webhook (exactly what Stripe does in production).
 *
 * The server's renewal handler then emails the customer a signed upload link
 * for the new cycle.
 *
 * RUN:  STRIPE_TEST_KEY=sk_test_... node simulate_renewal.js
 */
const Stripe = require("stripe");
const fs = require("fs");
const path = require("path");

const key = process.env.STRIPE_TEST_KEY;
if (!key || !key.startsWith("sk_test")) {
  console.error("✖ Set STRIPE_TEST_KEY (sk_test_...) first.  e.g.  source ~/.ef_test_key");
  process.exit(1);
}
const s = new Stripe(key);

// context from the checkout step
const ctx = JSON.parse(fs.readFileSync("/tmp/ef_test_ctx.json", "utf8"));

// read the webhook signing secret the server verifies against (.env)
const envPath = path.join(__dirname, "..", "01_Code", "echoframe-backend", ".env");
let WHSEC = "";
for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
  const m = line.match(/^\s*STRIPE_WEBHOOK_SECRET\s*=\s*(.+)\s*$/);
  if (m) { WHSEC = m[1].trim().replace(/^["']|["']$/g, ""); break; }
}
if (!WHSEC) { console.error("✖ Could not read STRIPE_WEBHOOK_SECRET from .env"); process.exit(1); }

const SERVER = "http://localhost:8000/webhook/stripe";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  // 1) locate the subscription for this customer
  const subs = await s.subscriptions.list({ customer: ctx.customer, status: "all", limit: 1 });
  if (!subs.data.length) { console.error("✖ No subscription found for customer " + ctx.customer); process.exit(1); }
  console.log("Subscription:", subs.data[0].id, "(" + subs.data[0].status + ")");

  // 2) advance the test clock ~32 days  (= one fictional month)
  const clock = await s.testHelpers.testClocks.retrieve(ctx.clock);
  const target = clock.frozen_time + 32 * 24 * 3600;
  console.log("Fast-forwarding the test clock ~1 month...");
  await s.testHelpers.testClocks.advance(ctx.clock, { frozen_time: target });
  let st = "advancing";
  for (let i = 0; i < 60 && st !== "ready"; i++) {
    await sleep(1500);
    st = (await s.testHelpers.testClocks.retrieve(ctx.clock)).status;
  }
  console.log("Test clock:", st);

  // 3) find the renewal (subscription_cycle) invoice Stripe just generated
  let renewal = null;
  for (let i = 0; i < 25 && !renewal; i++) {
    const invs = await s.invoices.list({ customer: ctx.customer, limit: 10 });
    renewal = invs.data.find((inv) => inv.billing_reason === "subscription_cycle");
    if (!renewal) await sleep(1500);
  }
  if (!renewal) { console.error("✖ No subscription_cycle invoice appeared after advancing the clock."); process.exit(1); }
  // re-fetch with the price line expanded so the server can route the product
  renewal = await s.invoices.retrieve(renewal.id, { expand: ["lines.data.price"] });
  console.log("Renewal invoice:", renewal.id, "| reason:", renewal.billing_reason, "| status:", renewal.status);

  // 4) deliver it to the local server as a signed Stripe webhook
  const event = {
    id: "evt_test_" + Date.now(),
    object: "event",
    api_version: renewal.api_version || null,
    created: Math.floor(Date.now() / 1000),
    type: "invoice.payment_succeeded",
    data: { object: renewal },
  };
  const payload = JSON.stringify(event);
  const sig = s.webhooks.generateTestHeaderString({ payload, secret: WHSEC });
  const res = await fetch(SERVER, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Stripe-Signature": sig },
    body: payload,
  });
  const text = await res.text();

  console.log("\nPOST /webhook/stripe ->", res.status, text);
  if (res.status === 200) {
    console.log("\n✓ Renewal delivered. The server just emailed the upload link to:", ctx.email);
    console.log("  Look for: \"Send me this month's numbers — your Auto Ledger\"  (check Gmail).");
  } else {
    console.log("\n✖ Server rejected the webhook — check /tmp/ef_server.log");
  }
})().catch((e) => { console.error("✖ ERROR:", e.message); process.exit(1); });
