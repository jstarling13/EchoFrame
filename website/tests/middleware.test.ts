import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { middleware } from "../middleware";

function requestWithAuth(auth?: string): NextRequest {
  const headers = new Headers();
  if (auth) headers.set("authorization", auth);
  return new NextRequest("https://example.com/admin/invoice", { headers });
}

describe("admin middleware — fails closed", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns 503 (not a challenge) when no password is configured, even with a guessed credential", () => {
    vi.stubEnv("ADMIN_INVOICE_PASSWORD", "");
    const withGuess = middleware(requestWithAuth(`Basic ${Buffer.from("admin:anything").toString("base64")}`));
    const withNothing = middleware(requestWithAuth());
    expect(withGuess.status).toBe(503);
    expect(withNothing.status).toBe(503);
  });

  it("returns 401 with a WWW-Authenticate challenge when configured but no credential is sent", () => {
    vi.stubEnv("ADMIN_INVOICE_PASSWORD", "correct-horse-battery-staple");
    const res = middleware(requestWithAuth());
    expect(res.status).toBe(401);
    expect(res.headers.get("WWW-Authenticate")).toMatch(/Basic/);
  });

  it("returns 401 for a wrong password", () => {
    vi.stubEnv("ADMIN_INVOICE_PASSWORD", "correct-horse-battery-staple");
    const wrong = `Basic ${Buffer.from("admin:wrong-password").toString("base64")}`;
    const res = middleware(requestWithAuth(wrong));
    expect(res.status).toBe(401);
  });

  it("lets the request through for the correct password", () => {
    vi.stubEnv("ADMIN_INVOICE_PASSWORD", "correct-horse-battery-staple");
    const correct = `Basic ${Buffer.from("admin:correct-horse-battery-staple").toString("base64")}`;
    const res = middleware(requestWithAuth(correct));
    // NextResponse.next() has no special status of its own — 200 with no
    // body is what "let it through" looks like from this function alone.
    expect(res.status).toBe(200);
  });
});
