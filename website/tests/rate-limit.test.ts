import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { checkRateLimit, InMemoryRateLimitStore } from "../lib/rate-limit";

describe("checkRateLimit — in-memory fallback boundary", () => {
  beforeEach(() => {
    vi.stubEnv("RATE_LIMIT_STORE_URL", "");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "");
    vi.stubEnv("NODE_ENV", "test");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("allows exactly 5 requests in the window and rejects the 6th (boundary)", async () => {
    const identifier = `boundary-${Math.random()}`;
    const results = [];
    for (let i = 0; i < 6; i++) {
      results.push(await checkRateLimit(identifier));
    }
    expect(results.slice(0, 5).every((r) => r.success)).toBe(true);
    expect(results[5]!.success).toBe(false);
    expect(results[5]!.remaining).toBe(0);
    expect(results.every((r) => r.durable === false)).toBe(true);
  });

  it("tracks separate identifiers independently", async () => {
    const a = `id-a-${Math.random()}`;
    const b = `id-b-${Math.random()}`;
    for (let i = 0; i < 5; i++) await checkRateLimit(a);
    const bResult = await checkRateLimit(b);
    expect(bResult.success).toBe(true);
    expect(bResult.remaining).toBe(4);
  });
});

describe("checkRateLimit — durable store failure falls back to in-memory (fail open)", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("falls back to in-memory and flags non-durable when the store is unreachable", async () => {
    vi.stubEnv("RATE_LIMIT_STORE_URL", "https://example-durable-store.invalid");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "test-token");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    const result = await checkRateLimit(`store-down-${Math.random()}`);
    expect(result.durable).toBe(false);
    expect(result.success).toBe(true);
  });

  it("uses the durable store when it responds successfully", async () => {
    vi.stubEnv("RATE_LIMIT_STORE_URL", "https://example-durable-store.invalid");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [{ result: 1 }],
      })
    );

    const result = await checkRateLimit(`store-up-${Math.random()}`);
    expect(result.durable).toBe(true);
    expect(result.success).toBe(true);
    expect(result.remaining).toBe(4);
  });
});

describe("InMemoryRateLimitStore", () => {
  it("resets the count after the window elapses", async () => {
    vi.useFakeTimers();
    try {
      const store = new InMemoryRateLimitStore();
      expect(await store.increment("k", 1)).toBe(1);
      expect(await store.increment("k", 1)).toBe(2);
      vi.advanceTimersByTime(1500);
      expect(await store.increment("k", 1)).toBe(1); // window elapsed, counter reset
    } finally {
      vi.useRealTimers();
    }
  });
});
