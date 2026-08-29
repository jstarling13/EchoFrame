import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  markEventProcessedIfNew,
  InMemoryEventStore,
  DurableStoreRequiredError,
} from "../lib/idempotency";

describe("markEventProcessedIfNew — in-memory fallback (local dev/test only)", () => {
  beforeEach(() => {
    vi.stubEnv("RATE_LIMIT_STORE_URL", "");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "");
    vi.stubEnv("NODE_ENV", "test");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("processes a new event once and flags a duplicate delivery", async () => {
    const eventId = `evt_dup_${Math.random()}`;
    expect(await markEventProcessedIfNew(eventId)).toBe(true);
    expect(await markEventProcessedIfNew(eventId)).toBe(false); // duplicate
    expect(await markEventProcessedIfNew(eventId)).toBe(false); // duplicate again
  });

  it("handles out-of-order event delivery independently by event ID", async () => {
    // Simulates Stripe delivering a later-created event before an earlier
    // one. Dedup is per unique event ID, not sequence — both must process.
    const eventB = `evt_out_of_order_B_${Math.random()}`;
    const eventA = `evt_out_of_order_A_${Math.random()}`;

    expect(await markEventProcessedIfNew(eventB)).toBe(true);
    expect(await markEventProcessedIfNew(eventA)).toBe(true);
    // Each is independently deduplicated on redelivery, regardless of order.
    expect(await markEventProcessedIfNew(eventB)).toBe(false);
    expect(await markEventProcessedIfNew(eventA)).toBe(false);
  });

  it("simulates a process restart: a fresh in-memory store has no memory of prior events", async () => {
    const store = new InMemoryEventStore();
    const eventId = "evt_restart_sim";
    expect(await store.markIfNew(eventId, 60)).toBe(true);
    expect(await store.markIfNew(eventId, 60)).toBe(false);

    // "Restart" = a brand new store instance (as happens on every cold
    // start of a serverless function with no external memory).
    const storeAfterRestart = new InMemoryEventStore();
    expect(await storeAfterRestart.markIfNew(eventId, 60)).toBe(true);
  });

  it("treats an expired idempotency record as new again", async () => {
    vi.useFakeTimers();
    try {
      const store = new InMemoryEventStore();
      const eventId = "evt_expiry";
      expect(await store.markIfNew(eventId, 1)).toBe(true); // 1s TTL
      expect(await store.markIfNew(eventId, 1)).toBe(false); // still within TTL

      vi.advanceTimersByTime(1500); // past the 1s TTL

      expect(await store.markIfNew(eventId, 1)).toBe(true); // expired -> treated as new
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("markEventProcessedIfNew — production fail-closed guard", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("throws DurableStoreRequiredError in production without a durable store configured", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("RATE_LIMIT_STORE_URL", "");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "");

    await expect(markEventProcessedIfNew("evt_prod_no_store")).rejects.toThrow(
      DurableStoreRequiredError
    );
  });

  it("does not throw in production once a durable store URL/token are set (network call may still fail in this test env, but not with a config error)", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("RATE_LIMIT_STORE_URL", "https://example-durable-store.invalid");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "test-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: "1" }),
    }));

    await expect(markEventProcessedIfNew("evt_prod_with_store")).resolves.toBe(true);
    vi.unstubAllGlobals();
  });

  it("fails closed (throws) in production if the configured durable store is unreachable", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("RATE_LIMIT_STORE_URL", "https://example-durable-store.invalid");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "test-token");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    await expect(markEventProcessedIfNew("evt_prod_store_down")).rejects.toThrow();
    vi.unstubAllGlobals();
  });
});
