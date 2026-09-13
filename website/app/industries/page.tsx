import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import IndustrySelector from "@/components/IndustrySelector";
import { INDUSTRY_OPTIONS, INDUSTRY_CONTENT } from "@/lib/industrySelector";

export const metadata: Metadata = {
  title: "Industries",
  description:
    "See how EchoFrame approaches workflow automation across bookkeeping, professional services, real estate, construction, multi-entity businesses, and other operationally complex small businesses.",
};

export default function IndustriesPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/industries", label: "Industries" }]} />
        <h1>Repeated work appears in every industry. Controls are industry-specific.</h1>
        <p>
          EchoFrame does not automate regulated professional judgment simply
          because a model can produce an answer. Choose the closest fit
          below, or read the common workflows for each industry.
        </p>

        <IndustrySelector />

        <div style={{ marginTop: "3rem" }}>
          {INDUSTRY_OPTIONS.map((option) => {
            const content = INDUSTRY_CONTENT[option.slug];
            if (!content) return null;
            return (
              <div key={option.slug} className="card" style={{ marginTop: "1.5rem" }}>
                <h3>{option.label}</h3>
                <p className="hint">{content.message}</p>
                <ul>
                  {content.workflows.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
