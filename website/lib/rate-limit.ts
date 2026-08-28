/**
 * Minimal rate limiter for the contact form. If RATE_LIMIT_STORE_URL and
 * RATE_LIMIT_STORE_TOKEN are set (an Upstash Redis REST-compatible store),
 * limits are enforced durably across serverless instances. Otherwise this
 * falls back to an in-memory limiter that only protects a single running
 * instance — acceptable for local/dev, NOT sufficient for a multi-instance
 * production deployment. Configure a real store before launch.
 */

const WINDOW_SECONDS = 60;
const MAX_REQUESTS = 5;

const memoryStore = new Map<string, { count: number; resetAt: number }>();

async function limitWithUpstash(
  key: string,
  url: string,
  token: string
): Promise<{ success: boolean; remaining: number }> {
  const pipeline = [
    ["INCR", key],
    ["EXPIRE", key, String(WINDOW_SECONDS), "NX"],
  ];
  const res = await fetch(`${url}/pipeline`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(pipeline),
    cache: "no-store",
  });
  if (!res.ok) {
    // Fail closed on the side of allowing the request but log for observability.
    console.error("rate_limit_store_error", res.status);
    return { success: true, remaining: MAX_REQUESTS };
  }
  const data = (await res.json()) as Array<{ result: number }>;
  const count = data[0]?.result ?? 1;
  return { success: count <= MAX_REQUESTS, remaining: Math.max(0, MAX_REQUESTS - count) };
}

function limitInMemory(key: string): { success: boolean; remaining: number } {
  const now = Date.now();
  const entry = memoryStore.get(key);
  if (!entry || entry.resetAt < now) {
    memoryStore.set(key, { count: 1, resetAt: now + WINDOW_SECONDS * 1000 });
    return { success: true, remaining: MAX_REQUESTS - 1 };
  }
  entry.count += 1;
  return {
    success: entry.count <= MAX_REQUESTS,
    remaining: Math.max(0, MAX_REQUESTS - entry.count),
  };
}

export async function checkRateLimit(
  identifier: string
): Promise<{ success: boolean; remaining: number }> {
  const key = `contact-form:${identifier}`;
  const url = process.env.RATE_LIMIT_STORE_URL;
  const token = process.env.RATE_LIMIT_STORE_TOKEN;
  if (url && token) {
    try {
      return await limitWithUpstash(key, url, token);
    } catch (err) {
      console.error("rate_limit_store_unreachable", err);
      return limitInMemory(key);
    }
  }
  return limitInMemory(key);
}
