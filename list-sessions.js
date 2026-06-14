#!/usr/bin/env node
/**
 * list-sessions.js — list recent SANDBOX Checkout Sessions so you can grab a
 * real session_id to verify the /upload routing locally. Uses STRIPE_TEST_KEY.
 *
 *   node list-sessions.js
 */
const Stripe = require("stripe");
const key = process.env.STRIPE_TEST_KEY;
if (!key || !key.startsWith("sk_test")) {
  console.error("✖ Set STRIPE_TEST_KEY to your sandbox secret key first.");
  process.exit(1);
}
const stripe = new Stripe(key);

(async () => {
  const r = await stripe.checkout.sessions.list({ limit: 10, expand: ["data.line_items"] });
  if (!r.data.length) { console.log("No checkout sessions found in this sandbox yet."); return; }
  console.log("Recent sandbox checkout sessions (newest first):\n");
  for (const s of r.data) {
    const email = (s.customer_details && s.customer_details.email) || "—";
    const item  = (s.line_items && s.line_items.data[0] && s.line_items.data[0].description) || "—";
    console.log(`${s.status === "complete" ? "✓" : "·"} ${s.id}`);
    console.log(`    status=${s.status}  email=${email}  product=${item}`);
    console.log(`    → open: http://localhost:8000/upload?session_id=${s.id}\n`);
  }
  console.log("Pick a ✓ complete one and open its localhost URL once the server is running.");
})().catch(e => { console.error("✖", e.message); process.exit(1); });
