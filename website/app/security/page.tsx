import type { Metadata } from "next";
import Image from "next/image";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Security",
  description:
    "A practical control framework for AI-involved workflows: data classification, tool approval, access minimization, human review, failure testing, and offboarding.",
};

const CONTROLS = [
  "Classify information",
  "Approve tools and accounts",
  "Minimize access",
  "Require human review where consequences rise",
  "Test failure modes",
  "Document fallback",
  "Transfer or remove access at handoff",
];

export default function SecurityPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/security", label: "Security" }]} />
        <Image
          className="line-icon on-light"
          src="/images/icon-security-shield.png"
          alt=""
          width={56}
          height={56}
        />
        <h1>Useful AI begins with a clear data path.</h1>
        <ul>
          {CONTROLS.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
        <div className="callout callout-risk">
          <p>
            This is a practical control framework, not a claim of compliance
            certification. PHI use is prohibited until counsel and security
            confirm a compliant architecture and required agreements. No
            sensitive data is submitted to AI systems by default.
          </p>
        </div>
      </div>
    </main>
  );
}
