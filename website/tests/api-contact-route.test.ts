import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "../app/api/contact/route";

const validPayload = {
  name: "Jordan Lee",
  email: "jordan@example.com",
  company: "Example Co",
  role: "Operations Director",
  website: "https://example.com",
  employeeRange: "25-49",
  state: "NY",
  workflowProblem: "Invoice approvals take two weeks and nobody knows why.",
  urgency: "This quarter",
  referralSource: "Referral",
  consent: true,
};

function makeRequest(body: unknown, headers: Record<string, string> = {}) {
  return new NextRequest("http://localhost:3000/api/contact", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}

function uniqueIp() {
  return { "x-forwarded-for": `10.0.0.${Math.floor(Math.random() * 254) + 1}` };
}

describe("POST /api/contact — integration", () => {
  beforeEach(() => {
    vi.stubEnv("CRM_WEBHOOK_URL", "");
    vi.stubEnv("CRM_WEBHOOK_SECRET", "");
    vi.stubEnv("EMAIL_PROVIDER_API_KEY", "");
    vi.stubEnv("EMAIL_FROM", "");
    vi.stubEnv("LEAD_NOTIFICATION_EMAIL", "");
    vi.stubEnv("RATE_LIMIT_STORE_URL", "");
    vi.stubEnv("RATE_LIMIT_STORE_TOKEN", "");
    vi.stubEnv("NODE_ENV", "test");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("rejects an invalid payload with 400 and field errors", async () => {
    const res = await POST(makeRequest({}, uniqueIp()));
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.ok).toBe(false);
    expect(body.errors.name).toBeTruthy();
  });

  it("silently accepts a honeypot-filled (spam) submission without attempting delivery", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    vi.stubEnv("CRM_WEBHOOK_URL", "https://crm.example.invalid/webhook");

    const res = await POST(
      makeRequest({ ...validPayload, company_website: "http://spam.example" }, uniqueIp())
    );
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("local/dev no-op: neither CRM nor email configured still returns 200 outside production", async () => {
    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(body.leadId).toBeTruthy();
  });

  it("email-only: succeeds when email delivery succeeds", async () => {
    vi.stubEnv("EMAIL_PROVIDER_API_KEY", "test-key");
    vi.stubEnv("EMAIL_FROM", "noreply@example.com");
    vi.stubEnv("LEAD_NOTIFICATION_EMAIL", "sales@example.com");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));

    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(200);
    expect((await res.json()).ok).toBe(true);
  });

  it("CRM-only: succeeds when CRM delivery succeeds", async () => {
    vi.stubEnv("CRM_WEBHOOK_URL", "https://crm.example.invalid/webhook");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));

    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(200);
    expect((await res.json()).ok).toBe(true);
  });

  it("both configured, one fails (partial): still 200", async () => {
    vi.stubEnv("CRM_WEBHOOK_URL", "https://crm.example.invalid/webhook");
    vi.stubEnv("EMAIL_PROVIDER_API_KEY", "test-key");
    vi.stubEnv("EMAIL_FROM", "noreply@example.com");
    vi.stubEnv("LEAD_NOTIFICATION_EMAIL", "sales@example.com");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.includes("crm.example.invalid")) {
          return Promise.resolve({ ok: false, status: 500, json: async () => ({}) });
        }
        return Promise.resolve({ ok: true, json: async () => ({}) });
      })
    );

    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(200);
    expect((await res.json()).ok).toBe(true);
  });

  it("both configured, both fail, in production: 503 (does not present a normal success state)", async () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("CRM_WEBHOOK_URL", "https://crm.example.invalid/webhook");
    vi.stubEnv("EMAIL_PROVIDER_API_KEY", "test-key");
    vi.stubEnv("EMAIL_FROM", "noreply@example.com");
    vi.stubEnv("LEAD_NOTIFICATION_EMAIL", "sales@example.com");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }));

    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(503);
    expect((await res.json()).ok).toBe(false);
  });

  it("neither configured, in production: 503 (production requires at least one destination)", async () => {
    vi.stubEnv("NODE_ENV", "production");
    const res = await POST(makeRequest(validPayload, uniqueIp()));
    expect(res.status).toBe(503);
  });

  it("rate limits after 5 requests from the same identifier within the window", async () => {
    const headers = uniqueIp();
    let lastRes;
    for (let i = 0; i < 6; i++) {
      lastRes = await POST(makeRequest(validPayload, headers));
    }
    expect(lastRes!.status).toBe(429);
  });
});
