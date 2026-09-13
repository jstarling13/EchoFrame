import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "How to Evaluate an AI Automation Proposal Before You Buy It",
  description:
    "A buyer's checklist: the questions to ask about scope, baselines, human review, data flow, failure handling, ownership, and measurement before approving the work.",
};

const CHECKLIST = [
  "The current process is mapped.",
  "Baseline figures are labeled measured, reported, or estimated.",
  "Capacity is not presented as automatic cash savings.",
  "Data access and vendors are visible.",
  "Human approvals and exception owners are named.",
  "Edge cases, outages, and fallback are tested.",
  "Ownership and exit rights are written down.",
  "Maintenance costs and responsibilities are disclosed.",
  "Success will be measured over an agreed period.",
];

export default function ArticlePage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs
          trail={[
            { href: "/insights", label: "Insights" },
            {
              href: "/insights/evaluating-an-ai-automation-proposal",
              label: "Evaluating an AI Proposal",
            },
          ]}
        />
        <p className="hint">September 13, 2026 &middot; 7 min read</p>
        <h1>How to Evaluate an AI Automation Proposal Before You Buy It</h1>

        <p>
          An automation proposal should make the work more understandable
          before it makes the work more technical.
        </p>
        <p>
          If the proposal leads with model names, broad percentages, or a
          long software list but cannot explain the current workflow, the
          buyer is being asked to purchase confidence rather than evidence.
        </p>
        <p>Use these questions before approving the work.</p>

        <h2>What exact workflow is in scope?</h2>
        <p>
          Ask for the trigger, endpoint, frequency, volume, systems, owners,
          and exceptions. &ldquo;Automate bookkeeping&rdquo; is not a scope.
          &ldquo;Prepare store-level journal entries from an approved
          source file and route exceptions for review&rdquo; is closer.
        </p>

        <h2>What is the verified baseline?</h2>
        <p>
          Request current touch time, cycle time, correction work, volume,
          and operating cost. Ask which numbers were measured, which were
          reported, and which were estimated. If the seller cannot
          distinguish capacity from cash savings, treat the ROI claim
          cautiously.
        </p>

        <h2>Why is this tool appropriate?</h2>
        <p>
          The proposal should compare the requirements of the workflow with
          the tool&rsquo;s reliability, data handling, integration path,
          cost, and maintenance burden. Ask what simpler rules-based or
          native integration was considered before adding a model.
        </p>

        <h2>Where does human review remain?</h2>
        <p>
          Ask which actions proceed automatically, what threshold stops
          them, who approves material decisions, and who owns exceptions.
          Be especially careful around payments, accounting judgments,
          employment decisions, sensitive data, legal conclusions, and
          safety-critical actions.
        </p>

        <h2>What data leaves the business?</h2>
        <p>
          Request a plain-language data-flow diagram. Identify every
          vendor, what it receives, why it needs the data, how access is
          authenticated, whether the data is retained or used for training,
          and how the relationship can be terminated.
        </p>

        <h2>How will failure appear?</h2>
        <p>
          Silence is not monitoring. Ask how the system reports missing
          data, duplicates, partial completion, bad credentials, API
          outages, and model uncertainty. Require a manual fallback and a
          named person responsible for recovery.
        </p>

        <h2>How will the result be tested?</h2>
        <p>
          The test plan should cover the normal path and edge cases. Agree
          on acceptance criteria before launch. A live demonstration with
          one clean example is not an acceptance test.
        </p>

        <h2>Who owns the work?</h2>
        <p>
          The agreement should identify ownership of delivered code,
          configurations, documentation, accounts, credentials, and
          reusable consultant tools. Ask what happens if the relationship
          ends tomorrow. The business should be able to operate or replace
          the system without indefinite dependence on the original builder.
        </p>

        <h2>What will maintenance require?</h2>
        <p>
          Request a list of dependencies, expected recurring cost, update
          process, retesting triggers, and support terms. &ldquo;No
          maintenance&rdquo; is rarely credible when the workflow relies on
          external systems.
        </p>

        <h2>How will value be measured?</h2>
        <p>
          The proposal should name the baseline, measurement period,
          evidence owner, and limitations. Results from another client are
          context, not a guarantee.
        </p>

        <h2>Buyer checklist</h2>
        <ul>
          {CHECKLIST.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p>A strong proposal should survive these questions. A good consultant should welcome them.</p>

        <p style={{ marginTop: "2rem" }}>
          Ready to run your own workflow through this checklist? See{" "}
          <Link href="/services">Pricing and Every Service in Detail</Link> or{" "}
          <Link href="/contact">request a quote</Link>.
        </p>

        <h2>Sources</h2>
        <ul>
          <li>
            <a
              href="https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook"
              target="_blank"
              rel="noopener noreferrer"
            >
              NIST AI RMF Playbook
            </a>
          </li>
          <li>
            <a
              href="https://www.cisa.gov/securebydesign"
              target="_blank"
              rel="noopener noreferrer"
            >
              CISA Secure by Design
            </a>
          </li>
        </ul>
      </div>
    </main>
  );
}
