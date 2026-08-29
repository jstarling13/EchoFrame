import { describe, expect, it } from "vitest";
import { checkEarlyCancellation } from "../lib/subscription-term";

const DAY = 86400;
const MONTH = 30.44 * DAY;

describe("checkEarlyCancellation", () => {
  it("flags cancellation on day 1 of a 3-month term as within term", () => {
    const start = 1_000_000;
    const result = checkEarlyCancellation(start, start + DAY, 3);
    expect(result.isWithinInitialTerm).toBe(true);
    expect(result.initialTermMonths).toBe(3);
  });

  it("flags cancellation just before the term ends as within term", () => {
    const start = 1_000_000;
    const result = checkEarlyCancellation(start, start + 3 * MONTH - DAY, 3);
    expect(result.isWithinInitialTerm).toBe(true);
  });

  it("does not flag cancellation exactly at or after the term boundary", () => {
    const start = 1_000_000;
    const atBoundary = checkEarlyCancellation(start, start + 3 * MONTH, 3);
    expect(atBoundary.isWithinInitialTerm).toBe(false);

    const afterBoundary = checkEarlyCancellation(start, start + 4 * MONTH, 3);
    expect(afterBoundary.isWithinInitialTerm).toBe(false);
  });

  it("treats a cancellation timestamp before the start as zero elapsed (still within term)", () => {
    const start = 1_000_000;
    const result = checkEarlyCancellation(start, start - DAY, 3);
    expect(result.monthsElapsed).toBe(0);
    expect(result.isWithinInitialTerm).toBe(true);
  });

  it("respects a custom initial term length", () => {
    const start = 1_000_000;
    const result = checkEarlyCancellation(start, start + 2 * MONTH, 6);
    expect(result.isWithinInitialTerm).toBe(true);
  });
});
