import { describe, expect, it } from "vitest";
import {
  OFFERS,
  formatUsd,
  getOffer,
  getCheckoutMilestone,
  getInvoiceMilestones,
  getDueAtCheckoutUsd,
  getDisplayPriceUsd,
  sumMilestones,
} from "../lib/offers";

describe("offers business consistency", () => {
  it("matches the approved v1 commercial constants exactly", () => {
    expect(OFFERS.map((o) => [o.code, o.name, o.totalUsd])).toEqual([
      ["O1", "Workflow Opportunity Diagnostic", 2500],
      ["O2", "Workflow Build Sprint", 7500],
      ["O3", "AI Operations Transformation", 18000],
      ["O4", "Enterprise AI Operations Program", 45000],
      ["O5", "Workflow Assurance & Enablement", null],
    ]);
  });

  it("gives every offer a unique route slug and Stripe checkout env var", () => {
    const slugs = OFFERS.map((o) => o.slug);
    const envVars = OFFERS.map((o) => o.stripeCheckoutPriceEnvVar);
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

describe("payment architecture — exact amounts charged at checkout (defect regression)", () => {
  // These lock in the corrected payment table from the pre-merge audit.
  // A prior version of this codebase would have charged the FULL contract
  // price for O2-O4 at checkout instead of the deposit. Every amount below
  // must come from server-controlled offer data, never a client input.

  it("O1: single checkout payment of $2,500 (no invoice milestones)", () => {
    const offer = getOffer("O1");
    expect(getDueAtCheckoutUsd(offer)).toBe(2500);
    expect(getDisplayPriceUsd(offer)).toBe(2500);
    expect(getInvoiceMilestones(offer)).toEqual([]);
    expect(sumMilestones(offer)).toBe(offer.totalUsd);
  });

  it("O2: $3,750 due at checkout; $3,750 final payment invoiced before launch", () => {
    const offer = getOffer("O2");
    expect(getDueAtCheckoutUsd(offer)).toBe(3750);
    expect(getDisplayPriceUsd(offer)).toBe(7500);
    const invoiceMilestones = getInvoiceMilestones(offer);
    expect(invoiceMilestones).toHaveLength(1);
    expect(invoiceMilestones[0]).toMatchObject({
      amountUsd: 3750,
      trigger: "Before production launch",
    });
    expect(sumMilestones(offer)).toBe(7500);
  });

  it("O3: $7,200 deposit due at checkout; $5,400 blueprint + $5,400 launch invoiced", () => {
    const offer = getOffer("O3");
    expect(getDueAtCheckoutUsd(offer)).toBe(7200);
    expect(getDisplayPriceUsd(offer)).toBe(18000);
    const invoiceMilestones = getInvoiceMilestones(offer);
    expect(invoiceMilestones.map((m) => m.amountUsd)).toEqual([5400, 5400]);
    expect(invoiceMilestones.map((m) => m.trigger)).toEqual([
      "After blueprint approval",
      "Before launch",
    ]);
    expect(sumMilestones(offer)).toBe(18000);
  });

  it("O4: $13,500 deposit due at checkout; $11,250 + $11,250 + $9,000 invoiced", () => {
    const offer = getOffer("O4");
    expect(getDueAtCheckoutUsd(offer)).toBe(13500);
    expect(getDisplayPriceUsd(offer)).toBe(45000);
    const invoiceMilestones = getInvoiceMilestones(offer);
    expect(invoiceMilestones.map((m) => m.amountUsd)).toEqual([11250, 11250, 9000]);
    expect(invoiceMilestones.map((m) => m.trigger)).toEqual([
      "After blueprint approval",
      "After implementation acceptance",
      "Before final handoff",
    ]);
    expect(sumMilestones(offer)).toBe(45000);
  });

  it("O5: $2,500/month due at checkout, no fixed total, 3-month initial term = $7,500 minimum", () => {
    const offer = getOffer("O5");
    expect(offer.billing).toBe("recurring");
    expect(getDueAtCheckoutUsd(offer)).toBe(2500);
    expect(getDisplayPriceUsd(offer)).toBe(2500);
    expect(offer.totalUsd).toBeNull();
    expect(offer.initialTermMonths).toBe(3);
    expect(offer.initialTermTotalUsd).toBe(7500);
    expect(getInvoiceMilestones(offer)).toEqual([]);
  });

  it("every offer has exactly one checkout milestone", () => {
    for (const offer of OFFERS) {
      expect(() => getCheckoutMilestone(offer)).not.toThrow();
      const checkoutMilestones = offer.milestones.filter((m) => m.method === "checkout");
      expect(checkoutMilestones).toHaveLength(1);
    }
  });

  it("one-time offers' milestones sum exactly to totalUsd (no rounding drift)", () => {
    for (const offer of OFFERS) {
      if (offer.billing === "one_time") {
        expect(sumMilestones(offer)).toBe(offer.totalUsd);
      }
    }
  });

  it("no milestone amount is ever equal to the full contract total except when there is only one milestone", () => {
    // Regression guard for the specific defect: Checkout must not be able
    // to charge the full O2/O3/O4 price. Any milestone with method
    // "checkout" whose amount equals totalUsd is only valid when the
    // offer has just that one milestone (O1's "100% prepaid" case).
    for (const offer of OFFERS) {
      if (offer.totalUsd === null) continue;
      const checkout = getCheckoutMilestone(offer);
      if (checkout.amountUsd === offer.totalUsd) {
        expect(offer.milestones).toHaveLength(1);
      }
    }
  });
});
