import path from "node:path";
import type { NextConfig } from "next";

/**
 * CSP note (pre-merge audit, 2026-08-29): a nonce-based CSP was tried via
 * middleware.ts so script-src could avoid 'unsafe-inline'. It was reverted
 * after testing showed two problems specific to this Next.js version:
 *
 * 1. Next only propagates the per-request nonce to a page's scripts (both
 *    its own inline hydration payloads AND its external /_next/static/
 *    chunk loaders) when something in that page's render tree actually
 *    calls headers() — there is no way to opt in globally without making
 *    literally every route dynamic (no more static generation at all,
 *    since the root layout wraps every page).
 * 2. Without the nonce reaching a page, our CSP blocked Next's own inline
 *    hydration scripts outright, which showed up as real, user-visible
 *    console errors ("Executing inline script violates CSP...", plus a
 *    React hydration error) — a genuine functional defect, not just a
 *    lint nitpick, caught via a Lighthouse run in this audit.
 *
 * Given this is a static marketing/lead-gen site with no user-generated
 * content ever rendered as raw HTML (the only dangerouslySetInnerHTML use
 * is our own server-authored JSON-LD, not user input — see
 * components/OfferDetail.tsx), 'unsafe-inline' on script-src is an
 * accepted, low-risk trade-off here, consistent with style-src already
 * using 'unsafe-inline'. Everything else in this policy stays strict
 * (no unsafe-eval, no wildcard hosts, frame-ancestors 'none', restricted
 * connect-src/form-action). Revisit if the site ever adds a real
 * user-generated-HTML sink.
 */
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data:",
      "font-src 'self'",
      "connect-src 'self'",
      "form-action 'self' https://checkout.stripe.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "object-src 'none'",
      "upgrade-insecure-requests",
    ].join("; "),
  },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  turbopack: {
    // Pin the workspace root to this project. Without this, Next.js walks
    // up looking for lockfiles and finds an unrelated package.json/
    // package-lock.json in the user's home directory (a stray file from a
    // different, unrelated project), which is outside this Git repo.
    root: path.resolve(__dirname),
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
  async redirects() {
    return [];
  },
};

export default nextConfig;
