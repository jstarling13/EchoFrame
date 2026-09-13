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
  {
    title: "Data Handling & Storage",
    body: "Data in transit is encrypted by default, and access is scoped to what a given workflow actually requires — not warehoused 'just in case.' At the end of an engagement, you decide what happens to EchoFrame's access: fully transferred to your team, revoked entirely, or something in between, documented in writing either way.",
  },
  {
    title: "Incident Response",
    body: "If a workflow misfires, a vendor has an outage, or something looks wrong with the data, you hear about it directly from me as soon as I've confirmed it — not through a support ticket, and not after the fact. Every production workflow has an agreed manual fallback so the business can keep operating while an issue gets fixed.",
  },
  {
    title: "Direct Accountability, No Middle Layer",
    body: "There is no subcontractor, offshore team, or support queue between you and the person who built your workflow. One person scopes it, builds it, tests it, and stays reachable for it — you are never re-explaining your business to someone new.",
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
          Every engagement operates under the same control framework,
          regardless of industry or workflow. No engagement is ever
          &ldquo;completely safe&rdquo; &mdash; no honest consultant would
          claim that. What EchoFrame can control is being direct about
          exactly what protects your data, what still depends on your own
          judgment, and what to do if something goes wrong.
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
