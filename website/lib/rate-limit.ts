/**
 * Rate limiter for the public contact form.
 *
 * PRODUCTION SAFETY: unlike Stripe webhook idempotency (lib/idempotency.ts,
 * which fails CLOSED), rate limiting fails OPEN when a durable store isn't
 * configured or is unreachable — a public lead-capture form staying
 * available matters more than perfect abuse protection for one instance.
 * But a missing durable store in production is loudly flagged in logs
 * every time, per the pre-merge audit's "public contact-form deployment
 * must also flag missing durable rate limiting" requirement. Configure
 * RATE_LIMIT_STORE_URL/RATE_LIMIT_STORE_TOKEN before real traffic —
 * without it, limits only apply per serverless instance, which is easy to
 * defeat at scale.
 */
import { isDurableStoreConfigured, isProductionRuntime } from "./durable-store";

const WINDOW_SECONDS = 60;
const MAX_REQUESTS = 5;

export interface RateLimitResult {
  success: boolean;
  remaining: number;
  /** False whenever this result came from the in-memory fallback, not the durable store. */
  durable: boolean;
}

export interface RateLimitStore {
  /** Increments the counter for `key` (creating it with the given TTL if absent) and returns the new count. */
  increment(key: string, windowSeconds: number): Promise<number>;
}

export class UpstashRestRateLimitStore implements RateLimitStore {
  constructor(
    private readonly url: string,
    private readonly token: string
  ) {}

  async increment(key: string, windowSeconds: number): Promise<number> {
    const pipeline = [
      ["INCR", key],
      ["EXPIRE", key, String(windowSeconds), "NX"],
    ];
    const res = await fetch(`${this.url}/pipeline`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(pipeline),
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Upstash-compatible store returned status ${res.status}`);
    }
    const data = (await res.json()) as Array<{ result: number }>;
    return data[0]?.result ?? 1;
  }
}

/** Local development and tests ONLY — see module doc. */
export class InMemoryRateLimitStore implements RateLimitStore {
  private readonly counts = new Map<string, { count: number; resetAt: number }>();

  async increment(key: string, windowSeconds: number): Promise<number> {
    const now = Date.now();
    const entry = this.counts.get(key);
    if (!entry || entry.resetAt <= now) {
      this.counts.set(key, { count: 1, resetAt: now + windowSeconds * 1000 });
      return 1;
    }
    entry.count += 1;
    return entry.count;
  }
}

const memoryStore = new InMemoryRateLimitStore();

function getDurableStore(): RateLimitStore {
  const url = process.env.RATE_LIMIT_STORE_URL!;
  const token = process.env.RATE_LIMIT_STORE_TOKEN!;
  return new UpstashRestRateLimitStore(url, token);
}

function toResult(
  count: number,
  durable: boolean,
  maxRequests: number
): RateLimitResult {
  return {
    success: count <= maxRequests,
    remaining: Math.max(0, maxRequests - count),
    durable,
  };
}

export interface RateLimitOptions {
  /** Distinguishes this feature's counters from every other caller's. */
  namespace?: string;
  maxRequests?: number;
  windowSeconds?: number;
}

export async function checkRateLimit(
  identifier: string,
  options: RateLimitOptions = {}
): Promise<RateLimitResult> {
  const {
    namespace = "contact-form",
    maxRequests = MAX_REQUESTS,
    windowSeconds = WINDOW_SECONDS,
  } = options;
  const key = `${namespace}:${identifier}`;

  if (isDurableStoreConfigured()) {
    try {
      const count = await getDurableStore().increment(key, windowSeconds);
      return toResult(count, true, maxRequests);
    } catch (err) {
      console.error("rate_limit_store_unreachable", err);
      const count = await memoryStore.increment(key, windowSeconds);
      return toResult(count, false, maxRequests);
    }
  }

  if (isProductionRuntime()) {
    console.error("rate_limit_durable_store_missing_production", {
      feature: namespace,
    });
  }

  const count = await memoryStore.increment(key, windowSeconds);
  return toResult(count, false, maxRequests);
}
