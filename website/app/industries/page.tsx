import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Industries",
  description:
    "Initial focus includes professional services, property operations, construction, recruiting, architecture/engineering administration, hospitality, logistics, distribution, and family businesses.",
};

const INDUSTRIES = [
  "Professional services",
  "Property operations",
  "Construction",
  "Recruiting",
  "Architecture/engineering administration",
  "Hospitality",
  "Logistics",
  "Distribution",
  "Family businesses",
];

export default function IndustriesPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/industries", label: "Industries" }]} />
        <h1>Repeated work appears in every industry. Controls are industry-specific.</h1>
        <p>
          Initial focus includes professional services, property operations,
          construction, recruiting, architecture/engineering administration,
          hospitality, logistics, distribution, and family businesses. We do
          not automate regulated judgment simply because a model can produce
          an answer.
        </p>
        <div className="grid grid-3" style={{ marginTop: "1.5rem" }}>
          {INDUSTRIES.map((industry) => (
            <div className="card" key={industry}>
              <h3>{industry}</h3>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
