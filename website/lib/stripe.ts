import Stripe from "stripe";

let cachedClient: Stripe | null = null;

/**
 * Lazily constructed so the app can build/typecheck and serve non-payment
 * routes even before STRIPE_SECRET_KEY is configured. Throws only when a
 * route that actually needs Stripe is invoked without the key set.
 */
export function getStripeClient(): Stripe {
  if (cachedClient) return cachedClient;
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    throw new Error(
      "STRIPE_SECRET_KEY is not set. Configure it in the environment before using Stripe-backed routes."
    );
  }
  cachedClient = new Stripe(key, {
    apiVersion: "2026-08-26.dahlia",
    appInfo: { name: "practical-ai-operations-site" },
  });
  return cachedClient;
}
