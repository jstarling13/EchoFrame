import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DraftBanner from "@/components/DraftBanner";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AI Workflow Consulting, Implementation & Training | Practical AI Operations",
    template: "%s | Practical AI Operations",
  },
  description:
    "Vendor-neutral AI workflow consulting for established businesses: process mapping, implementation, testing, staff training, governance, and ownership transfer.",
  robots: { index: true, follow: true },
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
