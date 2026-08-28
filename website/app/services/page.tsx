import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import OfferTable from "@/components/OfferTable";
import Faq from "@/components/Faq";

export const metadata: Metadata = {
  title: "Services",
  description:
    "Five AI operations engagements, from a 10-day diagnostic to a full enterprise program. Choose the smallest engagement that can produce evidence.",
};

export default function ServicesPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/services", label: "Services" }]} />
        <h1>Choose the smallest engagement that can produce evidence.</h1>
        <OfferTable />
        <div className="callout" style={{ marginTop: "2rem" }}>
          <p>
            Additional workflow: from $2,500. Additional onsite day: $2,000
            plus approved travel. Additional training cohort: $1,250. Data
            cleanup/migration: scoped separately. Ten-hour support block:
            $2,000. Security/compliance specialist: pass-through or
            separately quoted.
          </p>
        </div>

        <h2 style={{ marginTop: "3rem" }}>Frequently asked questions</h2>
        <Faq />
      </div>
    </main>
  );
}
