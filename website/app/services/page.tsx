import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import ServicesGrid from "@/components/ServicesGrid";
import PricingModel from "@/components/PricingModel";
import EngagementJourney from "@/components/EngagementJourney";
import Faq from "@/components/Faq";

export const metadata: Metadata = {
  title: "Services",
  description:
    "Bookkeeping and financial workflow automation, process automation, staff training, and ongoing AI consulting for small businesses — billed hourly, no fixed packages.",
};

export default function ServicesPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/services", label: "Services" }]} />
        <p className="eyebrow">The Capability Stack</p>
        <h1>One Engagement Model. Whatever the Business Actually Needs.</h1>
        <p>
          No tiered SKUs to decode, no platform to license &mdash; every
          project is scoped to the real problem, engineered through The
          OWNED Method&trade;, and billed the same simple way.
        </p>
        <ServicesGrid />

        <h2 style={{ marginTop: "3rem" }}>How Engagement Works</h2>
        <PricingModel />

        <div style={{ marginTop: "3rem" }}>
          <EngagementJourney />
        </div>

        <h2 style={{ marginTop: "3rem" }}>Frequently asked questions</h2>
        <Faq />
      </div>
    </main>
  );
}
