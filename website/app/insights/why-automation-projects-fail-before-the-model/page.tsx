import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Why Most Automation Projects Fail Before the First Model Is Chosen",
  description:
    "The easiest part of an automation project is picking a tool — and picking it too early is what usually breaks the project.",
  // Held back from the /insights index and search indexing for now —
  // staggered for a later, real publish date. See lib/insights.ts.
  robots: { index: false, follow: false },
};

export default function ArticlePage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs
          trail={[
            { href: "/insights", label: "Insights" },
            {
              href: "/insights/why-automation-projects-fail-before-the-model",
              label: "Why Automation Projects Fail",
            },
          ]}
        />
        <p className="hint">September 13, 2026 &middot; 6 min read</p>
        <h1>Why Most Automation Projects Fail Before the First Model Is Chosen</h1>

        <p>
          The easiest part of an automation project is choosing a tool. It is
          also the part most likely to happen too early.
        </p>
        <p>
          A business sees a new model, a clever demonstration, or a
          competitor announcing an AI initiative. The natural response is to
          ask where that tool can be installed. That reverses the order of
          the work. Before choosing a model, the business needs to know what
          event starts the workflow, where the data comes from, which
          decisions are rules, which decisions require judgment, what
          happens when an input is missing, and who owns the result.
        </p>
        <p>
          If those facts are unclear, automation does not remove disorder.
          It executes disorder faster.
        </p>

        <h2>The process has to exist before it can be automated</h2>
        <p>
          Many workflows survive through undocumented human knowledge. One
          employee knows which spreadsheet is current, which vendor
          description maps to which account, which duplicate can be ignored,
          and when an owner needs to approve an exception. An automation
          sees none of that unless it is made explicit.
        </p>
        <p>
          That is why the first useful artifact is a current-state workflow
          record, not a software recommendation. It should show the trigger,
          inputs, systems, handoffs, decisions, exceptions, outputs, timing,
          and owners. The map will usually expose problems that have nothing
          to do with AI: inconsistent naming, duplicate sources, missing
          approvals, stale permissions, and rules that change depending on
          who is working.
        </p>
        <p>Fixing those conditions may create value before a model is involved.</p>

        <h2>Baselines turn enthusiasm into a decision</h2>
        <p>
          &ldquo;This takes too long&rdquo; is not a baseline. Record the
          volume, touch time, waiting time, correction time, frequency, and
          people involved. Then separate three ideas that are often blended
          together:
        </p>
        <ul>
          <li><strong>Capacity:</strong> hours returned to the team.</li>
          <li><strong>Cost avoidance:</strong> future spending the business no longer expects to incur.</li>
          <li><strong>Cash savings:</strong> an expense that actually disappears.</li>
        </ul>
        <p>
          Reclaimed capacity is valuable, but it is not automatically payroll
          savings. A credible automation proposal states which kind of value
          it expects to create and how that result will be measured.
        </p>

        <h2>Risk belongs in the design, not at the end</h2>
        <p>
          The National Institute of Standards and Technology&rsquo;s AI Risk
          Management Framework organizes AI risk work around governing,
          mapping, measuring, and managing. Its practical lesson applies
          even to small implementations: roles, context, measurement, and
          response cannot be postponed until after launch.
        </p>
        <p>Before selecting a tool, decide:</p>
        <ul>
          <li>What data the workflow may access</li>
          <li>Which actions require approval</li>
          <li>What confidence or dollar threshold triggers review</li>
          <li>What gets logged</li>
          <li>What happens during an outage</li>
          <li>How the business returns to manual operation</li>
          <li>Who is accountable for exceptions</li>
        </ul>
        <p>
          Those decisions narrow the technology choices. That is useful. A
          vendor-neutral process should eliminate tools that cannot meet the
          workflow&rsquo;s requirements.
        </p>

        <h2>A better first question</h2>
        <p>
          Do not begin with, &ldquo;Where can we use AI?&rdquo; Begin with,
          &ldquo;Which repeated workflow is expensive enough to examine,
          stable enough to map, and measurable enough to prove?&rdquo;
        </p>
        <p>
          Then observe the work. Establish the baseline. Identify the
          exceptions. Define the controls. Only after that should anyone
          choose the model, integration, or platform.
        </p>
        <p>
          That order is less exciting than a demo. It is also how an
          automation becomes an operating improvement instead of another
          subscription.
        </p>

        <h2>Sources</h2>
        <ul>
          <li>
            <a
              href="https://www.nist.gov/itl/ai-risk-management-framework"
              target="_blank"
              rel="noopener noreferrer"
            >
              NIST AI Risk Management Framework
            </a>
          </li>
          <li>
            <a
              href="https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf"
              target="_blank"
              rel="noopener noreferrer"
            >
              NIST Generative AI Profile
            </a>
          </li>
        </ul>

        <p style={{ marginTop: "2rem" }}>
          This mapping-first discipline is the &ldquo;Observe&rdquo; stage of{" "}
          <Link href="/method">The OWNED Method&trade;</Link> &mdash; see how
          each of the five stages produces a concrete deliverable.
        </p>
      </div>
    </main>
  );
}
