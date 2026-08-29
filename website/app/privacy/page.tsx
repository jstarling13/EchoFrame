import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Privacy policy for White Oak Operations.",
  // Attorney-review draft, not final — never indexed regardless of
  // environment, even once Production is otherwise indexable.
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/privacy", label: "Privacy" }]} />
        <h1>Privacy policy</h1>
        <div className="callout callout-risk">
          <p>
            <strong>Draft for attorney review.</strong> This page describes
            only what this site actually implements today. It is not yet
            approved by counsel and must be finalized before production
            launch. Counsel selection and governing law are not assumed
            from initial New York client geography alone — see{" "}
            <code>legal/ATTORNEY_REVIEW_REQUIRED.md</code>.
          </p>
        </div>

        <h2>What we collect</h2>
        <p>
          Fit-call form submissions (name, work email, company, role,
          optional company website, employee range, state, a description of
          your workflow, urgency, optional referral source, and your consent
          choice); basic request/device log data; and, if you pay online,
          payment references from Stripe. We do not collect anything beyond
          what is implemented — see <code>website/lib</code> for the exact
          data paths.
        </p>

        <h2>How we use it</h2>
        <p>
          To respond to your request, qualify the lead, route it to our CRM
          and a notification email, and troubleshoot the site.
        </p>

        <h2>Who we share it with</h2>
        <p>
          Service providers that operate this site: hosting (Vercel),
          payments (Stripe), transactional email, and whichever CRM the
          owner selects (see <code>strategy/OPEN_QUESTIONS.md</code>). We do
          not sell personal information.
        </p>

        <h2>AI processing</h2>
        <p>
          Form content is not processed by an AI system by default. If that
          changes, this section will be updated to describe it before it is
          implemented.
        </p>

        <h2>Your choices</h2>
        <p>
          You can ask us not to contact you, and ask what we hold about you,
          by using the privacy contact route below.
        </p>

        <h2>Contact</h2>
        <p className="owner-todo">
          Owner/counsel action needed: legal entity name, mailing address,
          a verified privacy contact email, retention schedule, and
          effective date must be supplied before this page is published to
          production. Placeholder facts are intentionally not included.
        </p>
      </div>
    </main>
  );
}
