import type { Metadata } from "next";
import Image from "next/image";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Security",
  description:
    "How EchoFrame approaches access, human review, sensitive data, tool selection, and practical controls in AI and workflow automation projects.",
};

const CONTROL_AREAS = [
  {
    title: "Human Accountability",
    body: "AI output is never treated as authoritative just because it's confident. Every workflow has a named system owner, a human reviewer, an approval threshold, and an exception owner.",
  },
  {
    title: "Data Minimization",
    body: "Only the data required for the workflow gets used. Sensitive information never reaches a model or vendor without client authorization, appropriate vendor terms, a documented reason, and a clear retention path.",
  },
  {
    title: "High-Risk Boundaries",
    body: "No autonomous clinical decisions, legal advice, investment recommendations, lending/underwriting, employment screening, safety-critical control, or financial commitments without approved human control.",
  },
  {
    title: "Least Privilege",
    body: "The lowest permissions necessary, always. No shared credentials. MFA wherever it's available.",
  },
  {
    title: "Auditability",
    body: "Material automated actions preserve a timestamp, the acting system, the input, the output, and the approval where one was required.",
  },
  {
    title: "Testing Before Launch",
    body: "Happy path, missing data, duplicate events, bad input, edge cases, model uncertainty, vendor/API outages, and a rollback or manual fallback path — all tested before anything goes live.",
  },
  {
    title: "Client Ownership",
    body: "Clients understand what the workflow does, what it depends on, how to stop it, where human review happens, and what ongoing maintenance it needs.",
  },
  {
    title: "Model Changes",
    body: "Production workflows don't get a newer model swapped in just because one exists. Material workflows are re-tested before any production dependency changes.",
  },
  {
    title: "Professional Review",
    body: "Where accounting, legal, clinical, security, or other professional judgment is required, that judgment stays with the appropriate licensed professional — not the model.",
  },
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
        <p>
          Every engagement operates under the same nine-part control
          framework, regardless of industry or workflow.
        </p>

        <div className="accordion" style={{ marginTop: "1.5rem" }}>
          {CONTROL_AREAS.map((area) => (
            <details key={area.title}>
              <summary>{area.title}</summary>
              <p style={{ marginBottom: 0 }}>{area.body}</p>
            </details>
          ))}
        </div>

        <div className="callout callout-risk" style={{ marginTop: "2rem" }}>
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
