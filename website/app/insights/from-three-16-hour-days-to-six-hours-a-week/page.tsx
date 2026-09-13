import type { Metadata } from "next";
import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "From Three 16-Hour Processing Days to Six Hours a Week",
  description:
    "An anonymized case study: a client-tracked 87.5% reduction in weekly processing time for a multi-location food-service accounting operation.",
};

const OWNED_METHOD_APPLICATION = [
  {
    stage: "Observe",
    body: "Before any tool was discussed, the actual weekly process was mapped step by step: what triggered it, which systems it touched, where the operator made judgment calls versus followed a fixed rule, and where the three 16-hour days were actually being spent. A workflow like this is rarely one uniform task — it's usually a sequence of smaller, repeatable actions (pulling source data, matching it against what QuickBooks already shows, entering what's missing, resolving what doesn't match) that only looks like one undifferentiated 16-hour block from the outside.",
  },
  {
    stage: "Weigh",
    body: "Not every repeated task is worth automating. The specific question here was whether the posting logic was stable enough — did the same categories of entries recur in a predictable way, or did the operator's judgment change the outcome often enough that automating the mechanics wouldn't actually save meaningful time? The manual process being long and tedious was necessary but not sufficient justification on its own; the process also had to be repeatable enough that automation wouldn't just move the same manual decisions somewhere else.",
  },
  {
    stage: "Navigate",
    body: "QuickBooks Desktop already has a supported, vendor-documented integration path — the Web Connector protocol, using qbXML for the actual data exchange. That mattered more than it might sound: an unsupported workaround (screen automation, undocumented API calls) would have created a fragile dependency on QuickBooks' internal implementation details, breakable by an ordinary software update. Building against the documented protocol meant the integration would keep working across normal QuickBooks updates, and meant the resulting journal entries would look, to QuickBooks and to anyone auditing the books later, exactly like entries a person had made by hand — not like output from an opaque external system.",
  },
  {
    stage: "Engineer",
    body: "The system was built as a SOAP service that QuickBooks Web Connector calls on a schedule, generating store-level qbXML journal-entry requests from the underlying source data and posting them through that same supported path. Because it's a scheduled, repeatable sync rather than a one-off script, the same process that ran the first week keeps running the same way afterward — the whole point was to remove repeated manual execution, not just to automate a single instance of it.",
  },
  {
    stage: "Demonstrate & Transfer",
    body: "The client kept tracking weekly processing time on their own after the system went live, which is what produced the before/after figures in this case study — the measurement wasn't a one-time demo number, it was the client's own ongoing record of what the workflow actually took, week over week, from June through September 2026.",
  },
];

const SCRUTINY_QUESTIONS = [
  "Was the baseline actually measured, or estimated after the fact to make the result look better?",
  "Is the reduction reported in time, in dollars, or in something vaguer like \"efficiency\" — and if it's dollars, how was time converted into a cash figure?",
  "Was the result audited by anyone besides the person who built the system and the client who benefits from it looking good?",
  "Does the claim generalize beyond \"this happened once, for one client, under one set of conditions\"?",
  "What does the vendor say the result does not prove? If the answer is nothing, that's itself a signal.",
];

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
        <p className="hint">Case Study &middot; September 13, 2026 &middot; 9 min read</p>
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
          A weekly reconciliation and posting process like this is rarely
          one undifferentiated task, even when it looks that way from the
          outside as &ldquo;three 16-hour days.&rdquo; In multi-location
          operations, it typically breaks down into a handful of recurring
          sub-tasks that repeat once per location, every cycle: pulling
          source records, matching them against what the accounting system
          already shows, entering whatever is missing, and resolving
          whatever doesn&rsquo;t match on the first pass. The exceptions are
          usually a small share of total transactions, but they are exactly
          the part that resists a simple find-and-replace fix, which is why
          this kind of process tends to survive as manual work long after
          the routine matching around it could, in principle, be automated.
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

        <h2>How the OWNED Method applied to this engagement</h2>
        <p>
          The five-stage framework behind every EchoFrame engagement isn&rsquo;t
          just a diagram on the <Link href="/method">Method page</Link>
          &nbsp;&mdash; here is what each stage actually meant for this
          specific workflow.
        </p>
        {OWNED_METHOD_APPLICATION.map((stage, index) => (
          <div key={stage.stage} style={{ marginBottom: "1.25rem" }}>
            <p style={{ fontWeight: 700, marginBottom: "0.35rem" }}>
              {index + 1}. {stage.stage}
            </p>
            <p style={{ marginTop: 0 }}>{stage.body}</p>
          </div>
        ))}

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
          <li>
            The observation window (June through September 2026) is roughly
            three months. It does not by itself establish that the result
            holds up across a full fiscal year, seasonal transaction-volume
            swings, or a change in the underlying business (a new location
            added, a new point-of-sale system, a change in bank or
            processor).
          </li>
          <li>
            A truly independent audit of a result like this would mean a
            third party, with no financial stake in the outcome, verifying
            the before-and-after time logs directly rather than relying on
            the client&rsquo;s own tracking relayed through EchoFrame. That
            has not happened here, and this case study does not claim it
            has.
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

        <h2>Questions worth asking about any case study like this</h2>
        <p>
          Not just this one &mdash; any vendor&rsquo;s. A results claim is
          only as strong as the answers to a short list of questions, and a
          vendor who won&rsquo;t answer them plainly is telling you
          something.
        </p>
        <ul>
          {SCRUTINY_QUESTIONS.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ul>
        <p>
          This case study is written to survive those questions: the
          baseline and post-implementation figures were tracked by the
          client, not estimated after the fact; the reduction is reported in
          time, not converted into an unverified dollar figure; it has not
          been independently audited, and that limitation is stated plainly
          rather than omitted; it does not claim to generalize beyond this
          one engagement; and the &ldquo;What this result does not
          prove&rdquo; section above exists specifically so this page
          doesn&rsquo;t only say what the number means.
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
