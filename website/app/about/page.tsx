import type { Metadata } from "next";
import Image from "next/image";
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
          White Oak Operations is the selected working company name,
          pending trademark, entity-name, domain, and common-law clearance
          (strategy/DECISION_LOG.md). Legal entity type, formation state,
          and registered agent have not been finalized and are
          intentionally omitted here rather than fabricated.
        </p>

        <div className="grid grid-2" style={{ marginTop: "1.5rem" }}>
          <div className="card">
            <h3>Address</h3>
            <p>
              17 Ridgeway Drive
              <br />
              Cataula, GA 31804
            </p>
          </div>
          <div className="card">
            <h3>Contact</h3>
            <p>
              <a href="tel:+17063661096">(706) 366-1096</a>
              <br />
              <a href="mailto:jacobstarling4313@gmail.com">
                jacobstarling4313@gmail.com
              </a>
            </p>
          </div>
        </div>

        <div className="page-photo">
          <Image
            src="/images/about-office.png"
            alt=""
            fill
            sizes="(max-width: 768px) 100vw, 76rem"
          />
        </div>

        <div className="founder-section">
          <Image
            className="founder-photo"
            src="/assets/jacob-starling.jpg"
            alt="Jacob Starling, Founder of White Oak Operations"
            width={160}
            height={160}
          />
          <div>
            <p className="eyebrow">Jacob Starling, Founder</p>
            <h2>Capability, not dependency.</h2>
            <p>
              White Oak Operations exists to combine process consulting,
              implementation, training, and ownership transfer into one
              engagement, so a client team ends up able to run and extend
              its own workflow rather than depending on an outside vendor
              for it indefinitely.
            </p>
            <p className="owner-todo">
              Additional founder background and credentials are pending
              owner confirmation and are intentionally omitted here rather
              than fabricated.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
