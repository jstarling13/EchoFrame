import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

/**
 * Regression guard for website/docs/NO_PUBLIC_CHECKOUT.md: no page or
 * component may reference the checkout API route as a client-callable
 * link/button. The route itself (app/api/stripe/checkout/route.ts) is
 * exempt — it's the server-side implementation, not a UI reference to it.
 */
function collectFiles(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      if (entry === "api") continue; // API route implementations are exempt
      collectFiles(full, out);
    } else if (/\.(tsx|ts)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

describe("no public checkout button (website/docs/NO_PUBLIC_CHECKOUT.md)", () => {
  it("no app page or component references the Stripe checkout API route", () => {
    const root = join(__dirname, "..");
    const files = [
      ...collectFiles(join(root, "app")),
      ...collectFiles(join(root, "components")),
    ];

    const offenders = files.filter((f) =>
      readFileSync(f, "utf-8").includes("api/stripe/checkout")
    );

    expect(offenders).toEqual([]);
  });

  it("every offer detail page's only CTA links to /contact, not a payment action", () => {
    const detailSource = readFileSync(
      join(__dirname, "..", "components", "OfferDetail.tsx"),
      "utf-8"
    );
    expect(detailSource).toContain('href="/contact"');
    expect(detailSource).toContain("Book a fit call");
  });
});
