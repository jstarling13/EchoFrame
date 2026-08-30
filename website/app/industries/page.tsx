import type { Metadata } from "next";
import Image from "next/image";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Industries",
  description:
    "Initial focus includes professional services, property operations, construction, recruiting, architecture/engineering administration, hospitality, logistics, distribution, and family businesses.",
};

const INDUSTRIES = [
  { name: "Professional services", photo: "/images/industry-professional-services.png" },
  { name: "Property operations", photo: null },
  { name: "Construction", photo: null },
  { name: "Recruiting", photo: null },
  { name: "Architecture/engineering administration", photo: null },
  { name: "Hospitality", photo: null },
  { name: "Logistics", photo: "/images/industry-logistics.png" },
  { name: "Distribution", photo: null },
  { name: "Family businesses", photo: null },
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
            <div className="card" key={industry.name}>
              {industry.photo && (
                <div className="card-photo">
                  <Image src={industry.photo} alt="" fill sizes="(max-width: 768px) 100vw, 24rem" />
                </div>
              )}
              <h3>{industry.name}</h3>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
