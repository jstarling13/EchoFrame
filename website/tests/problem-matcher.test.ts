import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { matchProblem } from "../lib/problemMatcher";
import { PROBLEM_MATCHER_DOCUMENTS } from "../lib/problemMatcherCatalog";
import { SERVICE_CAPABILITIES } from "../lib/services";

describe("problemMatcher", () => {
  it("indexes only real, existing site copy — no invented text", () => {
    expect(PROBLEM_MATCHER_DOCUMENTS.length).toBeGreaterThan(0);
    for (const doc of PROBLEM_MATCHER_DOCUMENTS) {
      expect(doc.text.length).toBeGreaterThan(0);
    }
  });

  it("never indexes a raw internal slug as a standalone document", () => {
    for (const service of SERVICE_CAPABILITIES) {
      const raw = PROBLEM_MATCHER_DOCUMENTS.find((doc) => doc.text.trim() === service.slug);
      expect(raw).toBeUndefined();
    }
  });

  it("matches a description using terms from a known service", () => {
    const results = matchProblem(
      "we manually match bank deposits and reconcile cards every week",
      PROBLEM_MATCHER_DOCUMENTS,
    );
    expect(results.length).toBeGreaterThan(0);
    expect(results.some((r) => r.text.includes("Bookkeeping"))).toBe(true);
  });

  it("returns no results for a description with too few meaningful words", () => {
    expect(matchProblem("help", PROBLEM_MATCHER_DOCUMENTS)).toEqual([]);
    expect(matchProblem("", PROBLEM_MATCHER_DOCUMENTS)).toEqual([]);
  });

  it("returns no results for gibberish unrelated to any indexed content", () => {
    const results = matchProblem(
      "xkqz vroom bloop nonsense zxcv qwerty asdf",
      PROBLEM_MATCHER_DOCUMENTS,
    );
    expect(results).toEqual([]);
  });

  it("never returns more than one result per unique source string", () => {
    const results = matchProblem(
      "financial workflow automation reporting reconciliation",
      PROBLEM_MATCHER_DOCUMENTS,
    );
    const texts = results.map((r) => r.text);
    expect(new Set(texts).size).toBe(texts.length);
  });

  it("the deterministic matching engine makes no network request", () => {
    const root = join(__dirname, "..");
    for (const file of ["lib/problemMatcher.ts", "lib/problemMatcherCatalog.ts"]) {
      const source = readFileSync(join(root, file), "utf-8");
      expect(source).not.toMatch(/fetch\(|XMLHttpRequest|axios|\/api\//);
    }
  });
});
