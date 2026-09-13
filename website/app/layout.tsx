import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DraftBanner from "@/components/DraftBanner";
import { isProductionDeployment } from "@/lib/environment";

/**
 * NEXT_PUBLIC_SITE_URL is unset on the live Vercel project (no env vars are
 * configured there at all), so this must not fall back to localhost — that
 * literally shipped as the Open Graph image URL in production, breaking
 * every social-share preview. Production always resolves to the real
 * domain; Preview falls back to its Vercel-assigned URL; only local dev
 * falls back to localhost.
 */
const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ||
  (isProductionDeployment()
    ? "https://echoframe.net"
    : process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : "http://localhost:3000");

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AI Consulting for Small Businesses | EchoFrame",
    template: "%s | EchoFrame",
  },
  description:
    "EchoFrame builds practical AI and automation for small businesses — bookkeeping and financial workflows, process automation, and staff training. Billed hourly, no fixed packages.",
  // Preview/local builds must never be indexed. Individual routes (e.g.
  // /thank-you, /privacy, /terms) may narrow this further themselves.
  robots: isProductionDeployment()
    ? { index: true, follow: true }
    : { index: false, follow: false },
  openGraph: {
    type: "website",
    siteName: "EchoFrame",
    title: "EchoFrame | AI Implementation & Workflow Automation",
    description:
      "Practical AI implementation and workflow automation for small businesses.",
  },
  twitter: {
    card: "summary_large_image",
    title: "EchoFrame | AI Implementation & Workflow Automation",
    description:
      "Practical AI implementation and workflow automation for small businesses.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#content">
          Skip to content
        </a>
        <DraftBanner />
        <Header />
        <div id="content">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
