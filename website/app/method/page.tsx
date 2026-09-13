import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";
import MethodFlow from "@/components/MethodFlow";

export const metadata: Metadata = {
  title: "Method",
  description:
    "The OWNED Method™: EchoFrame's proprietary five-stage framework — Observe, Weigh, Navigate, Engineer, Demonstrate and transfer.",
};

const STEPS = [
  { title: "Observe", body: "Observe the real work, not the org chart's version of it." },
  { title: "Weigh", body: "Weigh value against risk before a single workflow is touched." },
  { title: "Navigate", body: "Navigate the architecture — vendor-neutral, evidence-led, never brand-first." },
  { title: "Engineer", body: "Engineer the controls, tests, and fallbacks into the build itself." },
  { title: "Demonstrate & Transfer", body: "Demonstrate measurable performance, train the team, and transfer full ownership." },
];

interface StageDetail {
  stage: string;
  deliverable: string;
  whatEchoFrameDoes: string;
  minimumContents: string[];
  acceptanceTest: string;
  decisionEnabled: string;
}

const STAGE_DETAILS: StageDetail[] = [
  {
    stage: "Observe",
    deliverable: "Current-State Workflow Record",
    whatEchoFrameDoes: "Maps the work as it actually happens",
    minimumContents: [
      "Start and end boundaries",
      "Step-by-step workflow map",
      "Systems and data touched",
      "Named role responsible for each step",
      "Observed timing and frequency",
      "Exception paths and workarounds",
      "Open facts that still need verification",
    ],
    acceptanceTest:
      "The people who perform the work recognize the map as accurate and correct any material omissions.",
    decisionEnabled: "Are we solving the real workflow or an idealized description of it?",
  },
  {
    stage: "Weigh",
    deliverable: "Opportunity and Risk Scorecard",
    whatEchoFrameDoes: "Tests value against operating risk",
    minimumContents: [
      "Baseline labor and cycle time",
      "Error, delay, concentration, and compliance exposure",
      "Data sensitivity and required approvals",
      "Estimated value range, with capacity separated from cash savings",
      "Feasibility, dependency, and maintenance assessment",
      "Automate, assist, defer, or decline recommendation",
    ],
    acceptanceTest:
      "Every claimed benefit traces to a baseline or is labeled as an assumption; every material risk has an owner or blocks the build.",
    decisionEnabled: "Is this workflow worth changing now?",
  },
  {
    stage: "Navigate",
    deliverable: "Solution Architecture and Control Plan",
    whatEchoFrameDoes: "Designs the data path, controls, and ownership model",
    minimumContents: [
      "System and data-flow diagram",
      "Build-versus-buy choices and rationale",
      "Permissions and data-minimization plan",
      "Human review and approval thresholds",
      "Exception, logging, retention, and failure paths",
      "Operating cost and vendor dependencies",
      "Ownership and exit plan",
    ],
    acceptanceTest:
      "The client can see what enters each system, what leaves it, who approves material actions, and how the workflow stops safely.",
    decisionEnabled: "What is the smallest defensible architecture?",
  },
  {
    stage: "Engineer",
    deliverable: "Tested Production Workflow",
    whatEchoFrameDoes: "Builds and tests the live workflow",
    minimumContents: [
      "Working integration or automation",
      "Versioned configuration and access list",
      "Tests for normal, missing, duplicate, malformed, and delayed inputs",
      "Vendor/API outage and rollback tests",
      "Action logs and error notifications",
      "Issue register with resolution status",
      "Launch checklist and approval",
    ],
    acceptanceTest:
      "Agreed tests pass, known limitations are documented, and the named owner can stop the workflow and use the fallback.",
    decisionEnabled: "Is this safe and reliable enough to enter live use?",
  },
  {
    stage: "Demonstrate & Transfer",
    deliverable: "Performance and Ownership Handoff Pack",
    whatEchoFrameDoes: "Measures performance and transfers operation",
    minimumContents: [
      "Before-and-after measurement report",
      "Limitations and unresolved risks",
      "Standard operating procedure",
      "Exception and recovery guide",
      "Role-based training materials",
      "Credential, vendor, and asset inventory",
      "Maintenance schedule and change log",
      "Ownership acceptance sign-off",
    ],
    acceptanceTest:
      "The client's designated owner completes a supervised run, handles a test exception, demonstrates the fallback, and confirms receipt of the assets and documentation.",
    decisionEnabled: "Can the client operate this system independently, and did the engagement produce a measurable result?",
  },
];

export default function MethodPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/method", label: "Method" }]} />
        <p className="eyebrow">The Case for Process Before Platform</p>
        <h1>The OWNED Method&trade;</h1>
        <p>
          Most automation initiatives fail before the first model is ever
          chosen &mdash; not from bad AI, but from skipping the discipline of
          understanding the process underneath it. The OWNED Method&trade;
          is EchoFrame&rsquo;s proprietary framework for closing that gap:
          five deliberate moves from diagnosis to full ownership transfer,
          engineered for measurable risk reduction at every stage.
        </p>
        <MethodFlow steps={STEPS} />

        <h2 style={{ marginTop: "3rem" }}>What Each Stage Delivers</h2>
        <p>
          Five stages are easy to name and easy to leave abstract. Here is
          the one concrete deliverable produced at each stage &mdash; not a
          verb, a physical artifact the client receives and can hold the
          engagement to.
        </p>
        <div className="offers-table-wrap">
          <table className="offers">
            <thead>
              <tr>
                <th>Stage</th>
                <th>What EchoFrame does</th>
                <th>What the client receives</th>
              </tr>
            </thead>
            <tbody>
              {STAGE_DETAILS.map((detail) => (
                <tr key={detail.stage}>
                  <td>{detail.stage}</td>
                  <td>{detail.whatEchoFrameDoes}</td>
                  <td>{detail.deliverable}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: "2.5rem" }}>
          {STAGE_DETAILS.map((detail) => (
            <div
              key={detail.stage}
              className="card"
              style={{ marginBottom: "1.5rem" }}
            >
              <p className="eyebrow">{detail.stage}</p>
              <h3 style={{ marginTop: 0 }}>{detail.deliverable}</h3>
              <p className="hint" style={{ marginTop: "-0.5rem" }}>
                {detail.whatEchoFrameDoes}
              </p>
              <p style={{ fontWeight: 700, marginBottom: "0.35rem" }}>
                Minimum contents
              </p>
              <ul style={{ marginTop: 0 }}>
                {detail.minimumContents.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p>
                <strong>Acceptance test:</strong> {detail.acceptanceTest}
              </p>
              <p style={{ marginBottom: 0 }}>
                <strong>Decision enabled:</strong> {detail.decisionEnabled}
              </p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
