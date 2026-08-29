import { afterEach, describe, expect, it, vi } from "vitest";
import { isProductionDeployment } from "../lib/environment";
import robots from "../app/robots";

describe("isProductionDeployment", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("is true only when VERCEL_ENV is exactly 'production'", () => {
    vi.stubEnv("VERCEL_ENV", "production");
    expect(isProductionDeployment()).toBe(true);
  });

  it("is false for preview", () => {
    vi.stubEnv("VERCEL_ENV", "preview");
    expect(isProductionDeployment()).toBe(false);
  });

  it("is false when unset (local dev)", () => {
    vi.stubEnv("VERCEL_ENV", "");
    expect(isProductionDeployment()).toBe(false);
  });
});

describe("robots.txt — Preview/local must never be crawlable", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("disallows everything outside Production", () => {
    vi.stubEnv("VERCEL_ENV", "preview");
    const result = robots();
    expect(result.rules).toEqual([{ userAgent: "*", disallow: "/" }] as never);
  });

  it("allows crawling (with exclusions) in Production", () => {
    vi.stubEnv("VERCEL_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://example.com");
    const result = robots();
    expect(result.sitemap).toBe("https://example.com/sitemap.xml");
    const rules = Array.isArray(result.rules) ? result.rules[0] : result.rules;
    expect(rules).toMatchObject({ userAgent: "*", allow: "/" });
  });
});
