/**
 * Tracks processed Stripe event IDs so retried/duplicate/out-of-order
 * webhook deliveries are handled safely (STRIPE_SPECIFICATION.md
 * "Webhooks": idempotent handler).
 *
 * PRODUCTION SAFETY: outside local development/tests, this module refuses
 * to silently fall back to in-memory state. If RATE_LIMIT_STORE_URL/
 * RATE_LIMIT_STORE_TOKEN (an Upstash Redis REST-compatible store) are not
 * configured, `markEventProcessedIfNew` throws `DurableStoreRequiredError`
 * — the webhook route must catch that and return an error response so
 * Stripe retries, rather than process the event without durable
 * dedup/idempotency. See website/docs/DURABLE_STORE.md.
 */
import {
  DurableStoreRequiredError,
  isDurableStoreConfigured,
  isProductionRuntime,
} from "./durable-store";

const EVENT_TTL_SECONDS = 60 * 60 * 24 * 7; // 7 days

/** True if this call is the first time `key` has been seen (i.e. it should be processed). */
export interface EventStore {
  markIfNew(key: string, ttlSeconds: number): Promise<boolean>;
}

/**
 * Upstash Redis REST-compatible store. `SET key 1 NX EX <ttl>` returns
 * null if the key already existed (duplicate), or the set value if it was
 * newly created (first time seen).
 */
export class UpstashRestEventStore implements EventStore {
  constructor(
    private readonly url: string,
    private readonly token: string
  ) {}

  async markIfNew(key: string, ttlSeconds: number): Promise<boolean> {
    const res = await fetch(
      `${this.url}/set/${encodeURIComponent(key)}/1/NX/EX/${ttlSeconds}`,
      { headers: { Authorization: `Bearer ${this.token}` }, cache: "no-store" }
    );
    if (!res.ok) {
      throw new Error(`Upstash-compatible store returned status ${res.status}`);
    }
    const data = (await res.json()) as { result: string | null };
    return data.result !== null;
  }
}

/**
 * In-memory store with real TTL expiry. Local development and tests
 * ONLY — a fresh instance (e.g. a new serverless invocation) has no
 * memory of previously seen events, and this must never be used in
 * production (enforced by markEventProcessedIfNew below).
 */
export class InMemoryEventStore implements EventStore {
  private readonly seenUntil = new Map<string, number>();

  async markIfNew(key: string, ttlSeconds: number): Promise<boolean> {
    const now = Date.now();
    const expiresAt = this.seenUntil.get(key);
    if (expiresAt !== undefined && expiresAt > now) {
      return false; // still within TTL: duplicate
    }
    this.seenUntil.set(key, now + ttlSeconds * 1000);
    return true; // new, or the previous record expired
  }
}

const memoryStore = new InMemoryEventStore();

function getDurableStore(): EventStore {
  const url = process.env.RATE_LIMIT_STORE_URL!;
  const token = process.env.RATE_LIMIT_STORE_TOKEN!;
  return new UpstashRestEventStore(url, token);
}

/**
 * @returns true if this event has not been processed before (process it),
 *          false if it's a duplicate delivery (acknowledge, do not reprocess).
 * @throws DurableStoreRequiredError if in production without a durable store configured.
 */
export async function markEventProcessedIfNew(eventId: string): Promise<boolean> {
  const key = `stripe-event:${eventId}`;

  if (isDurableStoreConfigured()) {
    try {
      return await getDurableStore().markIfNew(key, EVENT_TTL_SECONDS);
    } catch (err) {
      console.error("idempotency_store_unreachable", err);
      if (isProductionRuntime()) {
        // Fail closed: do NOT silently fall back to in-memory in
        // production, where it would not be shared across instances and
        // could let a duplicate event double-process. Let Stripe retry.
        throw err;
      }
      return memoryStore.markIfNew(key, EVENT_TTL_SECONDS);
    }
  }

  if (isProductionRuntime()) {
    throw new DurableStoreRequiredError("Stripe webhook idempotency");
  }

  return memoryStore.markIfNew(key, EVENT_TTL_SECONDS);
}

export { DurableStoreRequiredError };
