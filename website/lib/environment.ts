/**
 * "Is this literally the Production deployment" — distinct from
 * lib/durable-store.ts's `isProductionRuntime()` (NODE_ENV-based, true for
 * Preview too). This one is VERCEL_ENV-based and answers a narrower
 * question: search-engine indexing and live Stripe keys should only ever
 * be allowed on the real Production deployment, never Preview.
 *
 * `VERCEL_ENV` is "production" | "preview" | "development", set
 * automatically by Vercel; it is undefined when running locally, which
 * this treats as NOT production (correct — local dev must never index or
 * use live keys either).
 */
export function isProductionDeployment(): boolean {
  return process.env.VERCEL_ENV === "production";
}
