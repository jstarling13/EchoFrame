#!/usr/bin/env node
/**
 * clone-live-to-test.js
 * -----------------------------------------------------------------------------
 * Clones EchoFrame's LIVE Stripe catalog into TEST mode:
 *   - Products
 *   - Prices (one per product's active prices)
 *   - Payment Links (with live price IDs remapped to the new test price IDs)
 *
 * It is IDEMPOTENT: every object it creates in test mode is tagged with
 * metadata.cloned_from = <live_id>. On re-runs it skips anything already cloned,
 * so you can run it again after changing things in live to re-sync.
 *
 * It NEVER writes to your live account. Live key is used read-only.
 *
 * -----------------------------------------------------------------------------
 * SETUP (one time):
 *   npm init -y           # if you don't already have a package.json
 *   npm install stripe
 *
 * RUN:
 *   STRIPE_LIVE_KEY=sk_live_xxx STRIPE_TEST_KEY=sk_test_xxx node clone-live-to-test.js
 *
 *   # Preview without writing anything:
 *   STRIPE_LIVE_KEY=sk_live_xxx STRIPE_TEST_KEY=sk_test_xxx node clone-live-to-test.js --dry-run
 * -----------------------------------------------------------------------------
 */

const Stripe = require("stripe");

const LIVE_KEY = process.env.STRIPE_LIVE_KEY;
const TEST_KEY = process.env.STRIPE_TEST_KEY;
const DRY_RUN = process.argv.includes("--dry-run");

if (!LIVE_KEY || !LIVE_KEY.startsWith("sk_live")) {
  console.error("✖ STRIPE_LIVE_KEY must be set to your live secret key (sk_live_...).");
  process.exit(1);
}
if (!TEST_KEY || !TEST_KEY.startsWith("sk_test")) {
  console.error("✖ STRIPE_TEST_KEY must be set to your test secret key (sk_test_...).");
  process.exit(1);
}

const live = new Stripe(LIVE_KEY);
const test = new Stripe(TEST_KEY);

const livePriceRecurring = new Map(); // livePriceId -> boolean (is it a recurring price)

const log = (...a) => console.log(...a);
const tag = DRY_RUN ? "[dry-run] " : "";

// ----------------------------------------------------------------------------
// Helpers: build an index of already-cloned test objects by metadata.cloned_from
// ----------------------------------------------------------------------------
async function indexExisting(resource) {
  const map = new Map(); // cloned_from(liveId) -> test object
  for await (const obj of resource.list({ limit: 100 })) {
    const from = obj.metadata && obj.metadata.cloned_from;
    if (from) map.set(from, obj);
  }
  return map;
}

// ----------------------------------------------------------------------------
// 1. PRODUCTS
// ----------------------------------------------------------------------------
async function cloneProducts() {
  log("\n=== Products ===");
  const existing = await indexExisting(test.products);
  const liveToTestProduct = new Map();

  for await (const p of live.products.list({ active: true, limit: 100 })) {
    if (existing.has(p.id)) {
      liveToTestProduct.set(p.id, existing.get(p.id).id);
      log(`  • ${p.name}: already cloned -> ${existing.get(p.id).id}`);
      continue;
    }

    const params = {
      name: p.name,
      description: p.description || undefined,
      images: (p.images && p.images.length) ? p.images : undefined,
      tax_code: p.tax_code || undefined,
      url: p.url || undefined,
      unit_label: p.unit_label || undefined,
      metadata: { ...(p.metadata || {}), cloned_from: p.id },
    };

    if (DRY_RUN) {
      log(`  ${tag}create product: ${p.name}`);
      liveToTestProduct.set(p.id, `test_product_for_${p.id}`);
      continue;
    }

    const created = await test.products.create(params);
    liveToTestProduct.set(p.id, created.id);
    log(`  ✓ ${p.name} -> ${created.id}`);
  }
  return liveToTestProduct;
}

// ----------------------------------------------------------------------------
// 2. PRICES  (map live price id -> test price id; set default_price on product)
// ----------------------------------------------------------------------------
async function clonePrices(liveToTestProduct) {
  log("\n=== Prices ===");
  const existing = await indexExisting(test.prices);
  const liveToTestPrice = new Map();
  const defaultPriceByLiveProduct = new Map(); // liveProductId -> liveDefaultPriceId

  // remember each live product's default price so we can set it in test afterwards
  for await (const p of live.products.list({ active: true, limit: 100 })) {
    if (p.default_price) {
      defaultPriceByLiveProduct.set(
        p.id,
        typeof p.default_price === "string" ? p.default_price : p.default_price.id
      );
    }
  }

  for await (const price of live.prices.list({ active: true, limit: 100 })) {
    const liveProductId = typeof price.product === "string" ? price.product : price.product.id;
    const testProductId = liveToTestProduct.get(liveProductId);
    if (!testProductId) continue; // product wasn't cloned (inactive, etc.)

    livePriceRecurring.set(price.id, price.type === "recurring");

    if (existing.has(price.id)) {
      liveToTestPrice.set(price.id, existing.get(price.id).id);
      log(`  • price ${price.id}: already cloned -> ${existing.get(price.id).id}`);
      continue;
    }

    const params = {
      product: testProductId,
      currency: price.currency,
      metadata: { ...(price.metadata || {}), cloned_from: price.id },
      nickname: price.nickname || undefined,
      tax_behavior: price.tax_behavior && price.tax_behavior !== "unspecified"
        ? price.tax_behavior
        : undefined,
    };

    if (price.billing_scheme === "per_unit") {
      params.unit_amount = price.unit_amount;
    } else {
      params.billing_scheme = price.billing_scheme; // tiered, etc.
      if (price.tiers_mode) params.tiers_mode = price.tiers_mode;
    }

    if (price.type === "recurring" && price.recurring) {
      params.recurring = {
        interval: price.recurring.interval,
        interval_count: price.recurring.interval_count,
        usage_type: price.recurring.usage_type,
      };
      if (price.recurring.trial_period_days) {
        params.recurring.trial_period_days = price.recurring.trial_period_days;
      }
    }

    if (DRY_RUN) {
      const amt = price.unit_amount != null ? `$${(price.unit_amount / 100).toFixed(2)}` : price.billing_scheme;
      const rec = price.type === "recurring" ? `/${price.recurring.interval}` : " one-time";
      log(`  ${tag}create price for ${liveProductId}: ${amt}${rec}`);
      liveToTestPrice.set(price.id, `test_price_for_${price.id}`);
      continue;
    }

    const created = await test.prices.create(params);
    liveToTestPrice.set(price.id, created.id);
    log(`  ✓ price ${price.id} -> ${created.id}`);
  }

  // set default_price on each test product
  if (!DRY_RUN) {
    for (const [liveProductId, liveDefaultPriceId] of defaultPriceByLiveProduct) {
      const testProductId = liveToTestProduct.get(liveProductId);
      const testPriceId = liveToTestPrice.get(liveDefaultPriceId);
      if (testProductId && testPriceId) {
        try {
          await test.products.update(testProductId, { default_price: testPriceId });
        } catch (e) {
          log(`  ! could not set default_price on ${testProductId}: ${e.message}`);
        }
      }
    }
  }

  return liveToTestPrice;
}

// ----------------------------------------------------------------------------
// 3. PAYMENT LINKS  (remap line item prices into test)
// ----------------------------------------------------------------------------
async function clonePaymentLinks(liveToTestPrice) {
  log("\n=== Payment Links ===");
  const existing = await indexExisting(test.paymentLinks);
  const created = [];

  for await (const link of live.paymentLinks.list({ active: true, limit: 100 })) {
    if (existing.has(link.id)) {
      const url = existing.get(link.id).url;
      created.push({ liveId: link.id, url, reused: true });
      log(`  • ${link.id}: already cloned -> ${url}`);
      continue;
    }

    // fetch line items (each references a live price)
    const items = [];
    let unmapped = false;
    let hasRecurring = false;
    for await (const li of live.paymentLinks.listLineItems(link.id, { limit: 100 })) {
      const livePriceId = typeof li.price === "string" ? li.price : li.price.id;
      const testPriceId = liveToTestPrice.get(livePriceId);
      if (!testPriceId) {
        unmapped = true;
        log(`  ! ${link.id}: price ${livePriceId} not found in test — skipping link`);
        break;
      }
      if (livePriceRecurring.get(livePriceId)) hasRecurring = true;
      items.push({ price: testPriceId, quantity: li.quantity || 1 });
    }
    if (unmapped || items.length === 0) continue;

    // Rebuild after_completion cleanly — Stripe rejects an empty custom_message,
    // so only carry it over when it actually has a value.
    let afterCompletion;
    const ac = link.after_completion;
    if (ac && ac.type === "redirect" && ac.redirect && ac.redirect.url) {
      afterCompletion = { type: "redirect", redirect: { url: ac.redirect.url } };
    } else if (ac && ac.type === "hosted_confirmation") {
      afterCompletion = { type: "hosted_confirmation" };
      const cm = ac.hosted_confirmation && ac.hosted_confirmation.custom_message;
      if (cm) afterCompletion.hosted_confirmation = { custom_message: cm };
    }

    const params = {
      line_items: items,
      metadata: { ...(link.metadata || {}), cloned_from: link.id },
      after_completion: afterCompletion,
      allow_promotion_codes: link.allow_promotion_codes || undefined,
      automatic_tax: link.automatic_tax && link.automatic_tax.enabled
        ? { enabled: true }
        : undefined,
      billing_address_collection: link.billing_address_collection || undefined,
      phone_number_collection: link.phone_number_collection && link.phone_number_collection.enabled
        ? { enabled: true }
        : undefined,
      tax_id_collection: link.tax_id_collection && link.tax_id_collection.enabled
        ? { enabled: true }
        : undefined,
      submit_type: link.submit_type && link.submit_type !== "auto" ? link.submit_type : undefined,
    };

    // payment_method_collection and customer_creation are mutually exclusive by
    // price type: Stripe only allows the former on recurring links and the
    // latter on one-time links.
    if (hasRecurring) {
      if (link.payment_method_collection) {
        params.payment_method_collection = link.payment_method_collection;
      }
      if (link.subscription_data && link.subscription_data.description) {
        params.subscription_data = { description: link.subscription_data.description };
      }
    } else if (link.customer_creation) {
      params.customer_creation = link.customer_creation;
    }

    if (DRY_RUN) {
      log(`  ${tag}create payment link for ${link.id} (${items.length} line item[s])`);
      created.push({ liveId: link.id, url: "(dry-run, not created)", reused: false });
      continue;
    }

    try {
      const c = await test.paymentLinks.create(params);
      created.push({ liveId: link.id, url: c.url, reused: false });
      log(`  ✓ ${link.id} -> ${c.url}`);
    } catch (e) {
      log(`  ✖ ${link.id}: ${e.message}`);
    }
  }

  return created;
}

// ----------------------------------------------------------------------------
// main
// ----------------------------------------------------------------------------
(async () => {
  try {
    const liveAcct = await live.accounts.retrieve().catch(() => null);
    log(`Cloning LIVE → TEST${liveAcct ? ` for account ${liveAcct.id}` : ""}${DRY_RUN ? "  (DRY RUN)" : ""}`);

    const products = await cloneProducts();
    const prices = await clonePrices(products);
    const links = await clonePaymentLinks(prices);

    log("\n=== Summary ===");
    log(`Products mapped: ${products.size}`);
    log(`Prices mapped:   ${prices.size}`);
    log(`Payment links:   ${links.length}`);

    log("\n=== Test payment links (use these to run test purchases) ===");
    for (const l of links) log(`  ${l.url}`);

    log("\nUse Stripe test card 4242 4242 4242 4242, any future expiry, any CVC, any ZIP.");
    log("Done.");
  } catch (err) {
    console.error("\n✖ Failed:", err && err.message ? err.message : err);
    process.exit(1);
  }
})();
