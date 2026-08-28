import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Insights",
  description: "Notes on AI workflow implementation, governance, and training.",
};

export default function InsightsPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/insights", label: "Insights" }]} />
        <h1>Insights</h1>
        <p>
          No articles are published yet. This section is reserved for
          verified case studies and method notes, added only after real,
          confirmed engagement results — see{" "}
          <code>strategy/DECISION_LOG.md</code> on fabricated proof points.
        </p>
      </div>
    </main>
  );
}
