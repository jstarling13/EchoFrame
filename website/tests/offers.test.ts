import { describe, expect, it } from "vitest";
import { OFFERS, formatUsd, getOffer } from "../lib/offers";

describe("offers business consistency", () => {
  it("matches the approved v1 commercial constants exactly", () => {
    expect(OFFERS.map((o) => [o.code, o.name, o.priceUsd, o.depositUsd])).toEqual([
      ["O1", "Workflow Opportunity Diagnostic", 2500, 2500],
      ["O2", "Workflow Build Sprint", 7500, 3750],
      ["O3", "AI Operations Transformation", 18000, 7200],
      ["O4", "Enterprise AI Operations Program", 45000, 13500],
      ["O5", "Workflow Assurance & Enablement", 2500, 2500],
    ]);
  });

  it("gives every offer a unique route slug and Stripe env var", () => {
    const slugs = OFFERS.map((o) => o.slug);
    const envVars = OFFERS.map((o) => o.stripePriceEnvVar);
    expect(new Set(slugs).size).toBe(OFFERS.length);
    expect(new Set(envVars).size).toBe(OFFERS.length);
  });

  it("formats USD without decimals", () => {
    expect(formatUsd(2500)).toBe("$2,500");
    expect(formatUsd(45000)).toBe("$45,000");
  });

  it("throws on unknown offer code", () => {
    // @ts-expect-error intentional invalid input
    expect(() => getOffer("O9")).toThrow();
  });
});
