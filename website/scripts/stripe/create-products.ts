/**
 * Idempotently creates/updates Stripe Products and Prices in whichever mode
 * the provided key belongs to (test or live) from OFFERS in lib/offers.ts,
 * which mirrors /stripe/product_catalog.json.
 *
 * Only ONE Price is created per offer: the "checkout" milestone (deposit
 * for O2-O4, full amount for O1, monthly amount for O5). Later invoice
 * milestones (blueprint, acceptance, handoff, O2/O3/O4 final payment) are
 * deliberately NOT created as public Stripe Prices — per
 * STRIPE_SPECIFICATION.md "Object strategy", those are billed later by
 * staff via a Stripe Invoice against the signed SOW, using the printed
 * reference amounts below.
 *
 * This script never receives, prints, or transmits STRIPE_SECRET_KEY
 * anywhere except directly to the Stripe SDK — it must be run BY THE OWNER
 * with their own key already set in the environment:
 *
 *   STRIPE_SECRET_KEY=sk_test_... npm run stripe:sync
 *
 * Run with a test-mode key first and complete the STRIPE_SPECIFICATION.md
 * test matrix before ever running with a live-mode key. After it runs,
 * copy the printed Price IDs into your Vercel Environment Variables
 * (STRIPE_PRICE_O1 .. STRIPE_PRICE_O5_MONTHLY) — do not hardcode them.
 */
import Stripe from "stripe";
import {
  OFFERS,
  getCheckoutMilestone,
  getInvoiceMilestones,
  formatUsd,
} from "../../lib/offers";

async function main() {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    console.error(
      "STRIPE_SECRET_KEY is not set. Set it in your own shell/secret store and re-run:\n" +
        "  STRIPE_SECRET_KEY=sk_test_xxx npm run stripe:sync"
    );
    process.exit(1);
  }
  if (key.startsWith("sk_live_")) {
    console.warn(
      "\n*** WARNING: this is a LIVE-mode Stripe key. ***\n" +
        "Confirm the STRIPE_SPECIFICATION.md test matrix has passed and the\n" +
        "owner has explicitly approved live objects before continuing.\n" +
        "Press Ctrl+C within 5 seconds to abort.\n"
    );
    await new Promise((r) => setTimeout(r, 5000));
  }

  const stripe = new Stripe(key, { apiVersion: "2026-08-26.dahlia" });
  const results: { offer: string; productId: string; priceId: string; envVar: string }[] = [];

  for (const offer of OFFERS) {
    const milestone = getCheckoutMilestone(offer); // throws if offer data is malformed

    const existing = await stripe.products.search({
      query: `metadata['offer_code']:'${offer.code}'`,
    });

    const product =
      existing.data[0] ??
      (await stripe.products.create({
        name: offer.name,
        metadata: { offer_code: offer.code, source: "practical-ai-operations-site" },
      }));

    const existingPrices = await stripe.prices.list({ product: product.id, active: true });
    let price = existingPrices.data.find((p) =>
      offer.billing === "recurring"
        ? p.recurring?.interval === "month" && p.unit_amount === milestone.amountUsd * 100
        : !p.recurring && p.unit_amount === milestone.amountUsd * 100
    );

    if (!price) {
      price = await stripe.prices.create({
        product: product.id,
        currency: "usd",
        unit_amount: milestone.amountUsd * 100,
        ...(offer.billing === "recurring"
          ? { recurring: { interval: offer.interval ?? "month" } }
          : {}),
        metadata: { offer_code: offer.code, milestone_id: milestone.id },
      });
    }

    results.push({
      offer: offer.code,
      productId: product.id,
      priceId: price.id,
      envVar: offer.stripeCheckoutPriceEnvVar,
    });
  }

  console.log("\nStripe sync complete. Set these in Vercel > Project > Settings > Environment Variables:\n");
  for (const r of results) {
    console.log(`${r.envVar}=${r.priceId}   # ${r.offer} -> product ${r.productId}`);
  }

  console.log(
    "\nInvoice-only milestones (bill these manually via Stripe Invoices against the signed SOW — no public Price is created for them):\n"
  );
  for (const offer of OFFERS) {
    const invoiceMilestones = getInvoiceMilestones(offer);
    if (invoiceMilestones.length === 0) continue;
    console.log(`${offer.code} — ${offer.name}`);
    for (const m of invoiceMilestones) {
      console.log(`  ${m.label}: ${formatUsd(m.amountUsd)} — ${m.trigger}`);
    }
  }
}

main().catch((err) => {
  console.error("stripe_sync_failed", err);
  process.exit(1);
});
