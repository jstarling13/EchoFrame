import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "From Three 16-Hour Processing Days to Six Hours a Week",
  description:
    "An anonymized case study: a client-tracked 87.5% reduction in weekly processing time for a multi-location food-service accounting operation.",
};

export default function CaseStudyPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs
          trail={[
            { href: "/insights", label: "Insights" },
            {
              href: "/insights/from-three-16-hour-days-to-six-hours-a-week",
              label: "Case Study",
            },
          ]}
        />
        <p className="hint">Case Study &middot; September 13, 2026 &middot; 6 min read</p>
        <h1>From Three 16-Hour Processing Days to Six Hours a Week</h1>

        <p>
          A multi-location food-service accounting operation relied on one
          person to complete a weekly reconciliation and posting process by
          hand. EchoFrame rebuilt the workflow around QuickBooks
          Desktop&rsquo;s supported integration path, reducing a
          client-tracked weekly process from approximately 48 hours to
          approximately six hours.
        </p>

        <div className="offers-table-wrap">
          <table className="offers">
            <thead>
              <tr>
                <th>Measure</th>
                <th>Before</th>
                <th>After</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Weekly processing time</td>
                <td>Approximately 48 hours</td>
                <td>Approximately 6 hours</td>
              </tr>
              <tr>
                <td>Schedule</td>
                <td>Three 16-hour processing days</td>
                <td>Approximately two hours on each of those three days</td>
              </tr>
              <tr>
                <td>Reduction</td>
                <td colSpan={2}>42 hours per week &mdash; 87.5% of weekly processing time</td>
              </tr>
              <tr>
                <td>Locations supported</td>
                <td colSpan={2}>Multiple (exact count withheld to protect client anonymity)</td>
              </tr>
              <tr>
                <td>Observation period</td>
                <td>June 2026</td>
                <td>September 2026</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h2>The operating problem</h2>
        <p>
          The client supported the accounting process for a multi-location
          food-service business. Each week, one person manually moved
          information into QuickBooks and completed the related
          reconciliation and posting work. The process consumed three
          16-hour days, or approximately 48 hours each week.
        </p>
        <p>
          That burden was not merely an inconvenience. It concentrated an
          important financial process in one person, limited the capacity
          available for other work and higher-value review, and made the
          operation dependent on long manual processing days.
        </p>
        <p>
          The goal was not to &ldquo;add AI&rdquo; in the abstract. It was
          to remove repeatable data-entry work while keeping the accounting
          operator in control of review and exceptions.
        </p>

        <h2>Scope and intervention</h2>
        <p>
          EchoFrame built a full-stack accounting synchronization system
          using a SOAP service and the QuickBooks Web Connector protocol.
          The system generated store-level qbXML journal-entry requests and
          posted them through QuickBooks&rsquo; integration workflow,
          replacing the repeated manual creation of those entries across
          the client&rsquo;s locations.
        </p>

        <h2>What changed</h2>
        <p>
          From June through September 2026, the client tracked approximately
          six hours of weekly processing time after implementation,
          compared with approximately 48 hours before implementation. On
          those inputs, the workflow reclaimed approximately 42 hours per
          week &mdash; an 87.5% reduction in weekly processing time.
        </p>
        <p>
          That figure is a time-capacity result, not a guaranteed cash
          saving. EchoFrame has not established that 42 reclaimed hours
          produced a corresponding reduction in payroll or operating
          expense, and does not claim an 87.5% reduction in labor cost,
          headcount, accounting errors, or total bookkeeping work &mdash;
          only in the weekly processing time measured. The more accurate
          conclusion is that the system returned substantial weekly
          capacity to the operator.
        </p>

        <h2>Measurement method</h2>
        <ol>
          <li>
            <strong>Baseline:</strong> the client tracked one person working
            three 16-hour days on the manual process, approximately 48
            hours per week.
          </li>
          <li>
            <strong>Post-implementation:</strong> the client tracked
            approximately two hours on each of the same three processing
            days, approximately six hours per week.
          </li>
          <li>
            <strong>Calculation:</strong> (48 &minus; 6) / 48 = 87.5%.
          </li>
          <li>
            <strong>Observation window:</strong> approximately June through
            September 2026.
          </li>
          <li>
            <strong>Attribution:</strong> the figures were tracked by the
            client and relayed to EchoFrame. They were not independently
            audited.
          </li>
        </ol>

        <h2>What this result does not prove</h2>
        <ul>
          <li>This is one implementation for one client.</li>
          <li>The time figures were client-tracked but not independently audited.</li>
          <li>No formal pre/post error-rate study was conducted, and current accuracy has not been separately measured.</li>
          <li>No claim is made that reclaimed time equals realized cash savings.</li>
          <li>No claim is made that another business will achieve the same result.</li>
          <li>The client and any identifying business details are intentionally withheld.</li>
          <li>
            The system&rsquo;s performance may depend on the client&rsquo;s
            specific data structure, QuickBooks configuration, operating
            discipline, and exception volume.
          </li>
        </ul>

        <h2>What this case demonstrates</h2>
        <p>
          The useful lesson is not that every accounting process can be
          reduced by 87.5%. It is that a measurable workflow, with stable
          inputs and repeatable posting logic, can be redesigned around the
          work actually being done. The intervention began with the
          process, used the existing accounting system&rsquo;s integration
          path, and retained human involvement for the work that still
          required review.
        </p>

        <div className="callout" style={{ marginTop: "2rem" }}>
          <p className="eyebrow">Recommended public proof block</p>
          <p style={{ fontWeight: 700 }}>
            Approximately 42 hours of weekly processing capacity reclaimed.
          </p>
          <p style={{ marginBottom: 0 }}>
            For an anonymized multi-location food-service accounting
            operation, EchoFrame reduced a client-tracked weekly process from
            approximately 48 hours to approximately six hours, reclaiming
            roughly 42 hours of weekly capacity. The result was observed
            from June through September 2026, was not independently audited,
            and should not be interpreted as guaranteed savings or a typical
            result.
          </p>
        </div>

        <p style={{ marginTop: "2rem" }}>
          Read more on what a number like this does and does not mean in{" "}
          <Link href="/insights/what-an-87-5-percent-reduction-actually-required">
            What an 87.5% Reduction in Weekly Processing Time Actually
            Required
          </Link>
          , or see how this kind of engagement is scoped in{" "}
          <Link href="/method">The OWNED Method&trade;</Link>.
        </p>
      </div>
    </main>
  );
}
