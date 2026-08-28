/**
 * Tracks processed Stripe event IDs so retried/duplicate/out-of-order
 * webhook deliveries are handled safely (STRIPE_SPECIFICATION.md
 * "Webhooks": idempotent handler). Uses the same REST KV store as
 * lib/rate-limit.ts (RATE_LIMIT_STORE_URL/TOKEN, Upstash-compatible). Falls
 * back to an in-memory Set when unconfigured — fine for local testing, NOT
 * safe for a multi-instance production deployment. Configure a durable
 * store before live Stripe events are processed.
 */

const EVENT_TTL_SECONDS = 60 * 60 * 24 * 7; // 7 days
const memorySeen = new Set<string>();

export async function markEventProcessedIfNew(eventId: string): Promise<boolean> {
  const url = process.env.RATE_LIMIT_STORE_URL;
  const token = process.env.RATE_LIMIT_STORE_TOKEN;
  const key = `stripe-event:${eventId}`;

  if (url && token) {
    try {
      // SET key 1 NX EX <ttl> — returns null if the key already existed.
      const res = await fetch(
        `${url}/set/${encodeURIComponent(key)}/1/NX/EX/${EVENT_TTL_SECONDS}`,
        { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" }
      );
      if (!res.ok) {
        console.error("idempotency_store_error", res.status);
        return !memorySeenCheck(eventId);
      }
      const data = (await res.json()) as { result: string | null };
      return data.result !== null;
    } catch (err) {
      console.error("idempotency_store_unreachable", err);
      return !memorySeenCheck(eventId);
    }
  }

  return !memorySeenCheck(eventId);
}

function memorySeenCheck(eventId: string): boolean {
  const alreadySeen = memorySeen.has(eventId);
  memorySeen.add(eventId);
  return alreadySeen;
}
