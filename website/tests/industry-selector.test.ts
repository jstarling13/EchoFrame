import { describe, expect, it } from "vitest";
import {
  INDUSTRY_OPTIONS,
  PROBLEM_OPTIONS,
  INDUSTRY_CONTENT,
  PROBLEM_CONTENT,
  getSelectorResult,
  getOptionLabel,
} from "../lib/industrySelector";

describe("industrySelector", () => {
  it("has content for every industry and problem option", () => {
    for (const option of INDUSTRY_OPTIONS) {
      expect(INDUSTRY_CONTENT[option.slug]).toBeDefined();
    }
    for (const option of PROBLEM_OPTIONS) {
      expect(PROBLEM_CONTENT[option.slug]).toBeDefined();
    }
  });

  it("returns a result combining industry and problem content", () => {
    const result = getSelectorResult("accounting", "financial-workflows");
    expect(result).not.toBeNull();
    expect(result?.startingPoints.length).toBeGreaterThan(0);
    expect(result?.capabilities.length).toBeGreaterThan(0);
    expect(result?.firstQuestion).toBeTruthy();
  });

  it("returns null for unknown slugs", () => {
    expect(getSelectorResult("nope", "financial-workflows")).toBeNull();
    expect(getSelectorResult("accounting", "nope")).toBeNull();
  });

  it("looks up option labels", () => {
    expect(getOptionLabel(INDUSTRY_OPTIONS, "accounting")).toBe("Accounting & Bookkeeping");
    expect(getOptionLabel(PROBLEM_OPTIONS, "nope")).toBeUndefined();
  });
});
