import Stripe from "stripe";
import { isProductionDeployment } from "./environment";

let cachedClient: Stripe | null = null;

/**
 * Lazily constructed so the app can build/typecheck and serve non-payment
 * routes even before STRIPE_SECRET_KEY is configured. Throws only when a
 * route that actually needs Stripe is invoked without the key set.
 *
 * Also fails closed if a live-mode key (`sk_live_`) is used outside a
 * Vercel Production deployment. `VERCEL_ENV` is set automatically by
 * Vercel to "production" | "preview" | "development"; it is undefined
 * when running locally, which this treats as non-production. This exists
 * specifically so a live key accidentally pasted into Preview/Development
 * environment variables can never process a real charge there.
 */
export function getStripeClient(): Stripe {
  if (cachedClient) return cachedClient;

  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    throw new Error(
      "STRIPE_SECRET_KEY is not set. Configure it in the environment before using Stripe-backed routes."
    );
  }

  if (key.startsWith("sk_live_") && !isProductionDeployment()) {
    throw new Error(
      `Refusing to use a live-mode Stripe key outside Production (VERCEL_ENV=${process.env.VERCEL_ENV ?? "unset"}). ` +
        "Use a sk_test_ key in Development/Preview environment variables."
    );
  }

  cachedClient = new Stripe(key, {
    apiVersion: "2026-08-26.dahlia",
    appInfo: { name: "white-oak-operations-site" },
  });
  return cachedClient;
}

/** True if the configured Stripe key is a live-mode key. Used to gate UI/logging, never to bypass the guard above. */
export function isLiveStripeKeyConfigured(): boolean {
  return (process.env.STRIPE_SECRET_KEY ?? "").startsWith("sk_live_");
}
