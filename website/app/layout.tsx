import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DraftBanner from "@/components/DraftBanner";
import { isProductionDeployment } from "@/lib/environment";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AI Workflow Consulting, Implementation & Training | White Oak Operations",
    template: "%s | White Oak Operations",
  },
  description:
    "Vendor-neutral AI workflow consulting for established businesses: process mapping, implementation, testing, staff training, governance, and ownership transfer.",
  // Preview/local builds must never be indexed. Individual routes (e.g.
  // /thank-you, /privacy, /terms) may narrow this further themselves.
  robots: isProductionDeployment()
    ? { index: true, follow: true }
    : { index: false, follow: false },
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
