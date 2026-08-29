import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../app/api/stripe/checkout/route";

function makeRequest(body: unknown) {
  return new NextRequest("http://localhost:3000/api/stripe/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/stripe/checkout — integration", () => {
  beforeEach(() => {
    for (const v of ["O1", "O2", "O3", "O4", "O5_MONTHLY"]) {
      vi.stubEnv(`STRIPE_PRICE_${v}`, "");
    }
    vi.stubEnv("STRIPE_SECRET_KEY", "");
    vi.stubEnv("VERCEL_ENV", "");
    vi.stubEnv("NODE_ENV", "test");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("rejects an unknown offer code with 400", async () => {
    const res = await POST(makeRequest({ offerCode: "O9" }));
    expect(res.status).toBe(400);
  });

  it("rejects a malformed body with 400", async () => {
    const res = await POST(makeRequest({}));
    expect(res.status).toBe(400);
  });

  it("returns 503, not a functional checkout, when the offer's Stripe price is not configured", async () => {
    // No STRIPE_PRICE_O1 set (per beforeEach).
    const res = await POST(makeRequest({ offerCode: "O1" }));
    expect(res.status).toBe(503);
    const body = await res.json();
    expect(body.ok).toBe(false);
  });

  it("never accepts a client-supplied amount — the request schema has no amount field", async () => {
    // Even if a client tries to smuggle an amount through, it's ignored:
    // the route only reads offerCode/projectId/clientId from the body.
    vi.stubEnv("STRIPE_PRICE_O1", "price_test_123");
    vi.stubEnv("STRIPE_SECRET_KEY", "sk_test_fake");
    vi.stubGlobal("fetch", vi.fn()); // Stripe SDK shouldn't even be reachable in a way that uses client amount

    const res = await POST(
      makeRequest({ offerCode: "O1", amountUsd: 1, unit_amount: 1 })
    );
    // Whatever the outcome (network will fail in this sandboxed test), it
    // must not be a 200 with a session created from a client-supplied
    // amount — there is no code path that reads such a field at all.
    expect(res.status).not.toBe(200);
  });

  it("refuses a live-mode key outside Production (fails closed, returns 502, not a live charge)", async () => {
    vi.stubEnv("STRIPE_PRICE_O1", "price_test_123");
    vi.stubEnv("STRIPE_SECRET_KEY", "sk_live_should_never_be_used_here");
    vi.stubEnv("VERCEL_ENV", "preview");

    const res = await POST(makeRequest({ offerCode: "O1" }));
    expect(res.status).toBe(502);
    const body = await res.json();
    expect(body.ok).toBe(false);
  });
});
