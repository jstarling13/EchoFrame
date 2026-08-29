/**
 * Shared "is a durable store configured, and are we in a runtime where
 * that's mandatory" logic for lib/idempotency.ts and lib/rate-limit.ts.
 *
 * Production must not rely on in-memory state (a Vercel serverless
 * function's memory is not shared across instances and is not persisted
 * across cold starts/restarts). `NODE_ENV === "production"` is used as the
 * signal — not `VERCEL_ENV` — because Vercel sets `NODE_ENV=production`
 * for both Preview and Production deployments; only local `next dev`
 * (development) and the test runner (test) fall outside it, which is
 * exactly "local development and tests only" per the audit that added
 * this guard.
 */

export class DurableStoreRequiredError extends Error {
  constructor(featureName: string) {
    super(
      `${featureName} requires a durable store outside local development. ` +
        "Set RATE_LIMIT_STORE_URL and RATE_LIMIT_STORE_TOKEN (an Upstash " +
        "Redis REST-compatible store) in this environment's variables. " +
        "See .env.example and website/docs/DURABLE_STORE.md."
    );
    this.name = "DurableStoreRequiredError";
  }
}

export function isDurableStoreConfigured(): boolean {
  return Boolean(process.env.RATE_LIMIT_STORE_URL && process.env.RATE_LIMIT_STORE_TOKEN);
}

export function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production";
}

/** Throws DurableStoreRequiredError if running in production without a durable store configured. */
export function requireDurableStoreInProduction(featureName: string): void {
  if (isProductionRuntime() && !isDurableStoreConfigured()) {
    throw new DurableStoreRequiredError(featureName);
  }
}
