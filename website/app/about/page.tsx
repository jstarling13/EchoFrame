import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "About",
  description:
    "White Oak Operations combines process consulting, implementation, training, and ownership transfer. Vendor-neutral: tools are selected against the workflow, risk, evidence, cost, and exit path.",
};

export default function AboutPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/about", label: "About" }]} />
        <h1>Built for operators who want capability, not dependency.</h1>
        <p>
          White Oak Operations combines process consulting,
          implementation, training, and ownership transfer. The company is
          vendor-neutral: tools are selected against the workflow, risk,
          evidence, cost, and exit path.
        </p>
        <p className="owner-todo">
          Company name confirmed by the owner: White Oak Operations
          (strategy/DECISION_LOG.md). Trademark/domain clearance status has
          not been separately confirmed. Legal entity name, mailing
          address, phone, and support/privacy email have not been
          finalized and are intentionally omitted here rather than
          fabricated.
        </p>
      </div>
    </main>
  );
}
