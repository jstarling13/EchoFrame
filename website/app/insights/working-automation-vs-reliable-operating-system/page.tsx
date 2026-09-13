import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "A Working Automation Is Not Yet a Reliable Operating System",
  description:
    "A prototype proves a path can work. An operating system has to prove what happens when it doesn't.",
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
              href: "/insights/working-automation-vs-reliable-operating-system",
              label: "Working vs. Reliable",
            },
          ]}
        />
        <p className="hint">September 13, 2026 &middot; 6 min read</p>
        <h1>A Working Automation Is Not Yet a Reliable Operating System</h1>

        <p>
          A prototype proves that a path can work. An operating system has
          to prove what happens when it does not.
        </p>
        <p>
          That difference matters. A demonstration usually receives clean
          inputs, valid credentials, available vendors, and a person
          watching every step. Production receives duplicate events,
          missing fields, changed formats, expired credentials, network
          interruptions, and users who assume the system is working because
          no error appeared on screen.
        </p>

        <h2>Reliability begins with named ownership</h2>
        <p>Every material workflow needs four answers:</p>
        <ul>
          <li>Who owns the system?</li>
          <li>Who reviews the output?</li>
          <li>What requires approval?</li>
          <li>Who handles an exception?</li>
        </ul>
        <p>
          &ldquo;The AI handles it&rdquo; is not an answer. NIST&rsquo;s AI
          guidance emphasizes documenting roles and responsibilities for
          human oversight. In a small business, that can be simple, but it
          must be explicit.
        </p>

        <h2>Test the unhappy paths</h2>
        <p>A workflow is not ready because the normal case passed once. Test at least:</p>
        <ul>
          <li>Missing data</li>
          <li>Malformed data</li>
          <li>Duplicate submissions</li>
          <li>Unexpected values</li>
          <li>Delayed inputs</li>
          <li>Model uncertainty</li>
          <li>Expired credentials</li>
          <li>Vendor or API outage</li>
          <li>Partial completion</li>
          <li>Rollback and manual fallback</li>
        </ul>
        <p>
          For a financial action, also test whether the system can create a
          duplicate, post to the wrong entity or period, or continue after
          one step failed.
        </p>

        <h2>Make actions reconstructable</h2>
        <p>
          Material automated actions should leave enough evidence to
          answer: What happened? When? Which input caused it? Which system
          acted? What output was produced? Who approved it, if approval was
          required?
        </p>
        <p>
          Logging is not the same as collecting everything. Data
          minimization still applies. Keep the information needed to
          operate and investigate the workflow, protect it appropriately,
          and define how long it remains available.
        </p>

        <h2>Define the boundary of automation</h2>
        <p>
          Reliable systems do not automate every available decision. They
          separate deterministic execution from professional judgment. An
          automation may prepare an accounting entry, route an invoice, or
          flag an exception. The appropriate business owner or licensed
          professional remains responsible for judgment that the system is
          not authorized to make.
        </p>
        <p>
          Thresholds make that boundary operational. A low-risk, exact
          match may proceed automatically. A material amount, poor match,
          missing source, or unusual pattern may stop for review.
        </p>

        <h2>Plan for change</h2>
        <p>
          Models, APIs, formats, credentials, and vendor terms change. A
          newer model should not enter a production workflow merely because
          it exists. Material dependencies should be inventoried, changes
          should be tested, and the business should know how to return to
          the last working configuration.
        </p>

        <h2>Transfer the system, not just the login</h2>
        <p>
          Client ownership requires more than credentials. The owner needs
          an operating procedure, exception guide, data-flow record,
          permissions list, vendor inventory, maintenance schedule, and
          fallback. A successful handoff includes a supervised run in which
          the client handles an exception and demonstrates the manual
          recovery path.
        </p>
        <p>
          The standard is not perfection. It is controlled operation:
          failures become visible, responsibility is clear, and the
          business can continue when the automation cannot.
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
              href="https://www.cisa.gov/securebydesign"
              target="_blank"
              rel="noopener noreferrer"
            >
              CISA Secure by Design
            </a>
          </li>
          <li>
            <a
              href="https://www.gao.gov/products/gao-26-108633"
              target="_blank"
              rel="noopener noreferrer"
            >
              GAO Federal Information System Controls Audit Manual
            </a>
          </li>
        </ul>

        <p style={{ marginTop: "2rem" }}>
          These are the same controls behind EchoFrame&rsquo;s{" "}
          <Link href="/security">Security</Link> commitments and the
          &ldquo;Engineer&rdquo; and &ldquo;Demonstrate &amp; Transfer&rdquo;
          stages of <Link href="/method">The OWNED Method&trade;</Link>.
        </p>
      </div>
    </main>
  );
}
