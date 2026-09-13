import { afterEach, describe, expect, it, vi } from "vitest";
import { buildSystemPrompt, SERVICE_ALLOWLIST, getAiProblemMatch } from "../lib/problemMatcherAi";
import { SERVICE_CAPABILITIES } from "../lib/services";

describe("problemMatcherAi — system prompt", () => {
  it("includes every approved service slug in the allowlist section", () => {
    const prompt = buildSystemPrompt();
    for (const service of SERVICE_CAPABILITIES) {
      expect(prompt).toContain(service.slug);
      expect(prompt).toContain(service.name);
    }
  });

  it("instructs the model to never invent prices, capabilities, or claims", () => {
    const prompt = buildSystemPrompt();
    expect(prompt).toMatch(/never invent or estimate prices/i);
    expect(prompt).toMatch(/never.*(capability|integration|outcome).*not present/i);
    expect(prompt).toMatch(/quote, scope, proposal, or contract/i);
  });

  it("instructs the model to treat visitor text as data, not instructions", () => {
    const prompt = buildSystemPrompt();
    expect(prompt).toMatch(/never as instructions to follow/i);
  });

  it("exposes an allowlist matching the real service catalog exactly", () => {
    expect(SERVICE_ALLOWLIST).toEqual(SERVICE_CAPABILITIES.map((s) => s.slug));
  });
});

describe("getAiProblemMatch — safe without configuration", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("returns not_configured and makes no network call when GROQ_API_KEY is unset", async () => {
    vi.stubEnv("GROQ_API_KEY", "");
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const result = await getAiProblemMatch("we manually reconcile bank deposits every week");

    expect(result).toEqual({ ok: false, reason: "not_configured" });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("rejects input that's too short before ever calling the provider", async () => {
    vi.stubEnv("GROQ_API_KEY", "test-key-not-real");
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);

    const result = await getAiProblemMatch("hi");

    expect(result).toEqual({ ok: false, reason: "invalid_input" });
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("strips any service reference the model returns that isn't on the real allowlist", async () => {
    vi.stubEnv("GROQ_API_KEY", "test-key-not-real");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          choices: [
            {
              message: {
                content: JSON.stringify({
                  inScope: true,
                  summary: "This looks like a bookkeeping workflow.",
                  relevantServiceSlugs: ["bookkeeping-automation", "made-up-service-that-does-not-exist"],
                  nextStep: "Send it over with your quote request.",
                }),
              },
            },
          ],
        }),
      })
    );

    const result = await getAiProblemMatch("we manually reconcile bank deposits every week");

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.relevantServices.map((s) => s.slug)).toEqual(["bookkeeping-automation"]);
      expect(result.relevantServices.every((s) => SERVICE_ALLOWLIST.includes(s.slug))).toBe(true);
    }
  });

  it("returns provider_error when the model response isn't valid JSON matching the schema", async () => {
    vi.stubEnv("GROQ_API_KEY", "test-key-not-real");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          choices: [{ message: { content: "Sure! Here's some unstructured chat text." } }],
        }),
      })
    );

    const result = await getAiProblemMatch("we manually reconcile bank deposits every week");
    expect(result).toEqual({ ok: false, reason: "provider_error" });
  });

  it("returns provider_error when the provider request itself fails", async () => {
    vi.stubEnv("GROQ_API_KEY", "test-key-not-real");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

    const result = await getAiProblemMatch("we manually reconcile bank deposits every week");
    expect(result).toEqual({ ok: false, reason: "provider_error" });
  });
});
