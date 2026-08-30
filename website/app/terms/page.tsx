import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Terms of Use",
  description: "Website terms of use for White Oak Operations.",
  // Attorney-review draft, not final — never indexed regardless of
  // environment, even once Production is otherwise indexable.
  robots: { index: false, follow: true },
};

export default function TermsPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/terms", label: "Terms" }]} />
        <h1>Terms of use</h1>
        <div className="callout callout-risk">
          <p>
            <strong>Draft for attorney review.</strong> This page is a
            business-operating draft, not legal advice, and is not yet
            approved by counsel (see{" "}
            <code>legal/ATTORNEY_REVIEW_REQUIRED.md</code>). It must not be
            treated as final before that review. Governing law and venue
            are not assumed from initial New York client geography alone —
            see the factors below.
          </p>
        </div>

        <h2>Informational site</h2>
        <p>
          This site is informational. No professional advice is given
          through it, and no client relationship is formed until a signed
          agreement is in place.
        </p>

        <h2>Acceptable use</h2>
        <p>
          Do not misuse, scrape, interfere with, impersonate on, or submit
          unlawful content through this site or its forms.
        </p>

        <h2>Ownership</h2>
        <p>
          The site and its content are owned by White Oak Operations or
          its licensors, subject to third-party materials identified
          separately.
        </p>

        <h2>Disclaimers and liability</h2>
        <p>
          The site is provided without warranties beyond what applicable law
          requires, and liability is limited as counsel finalizes.
        </p>

        <h2>Changes</h2>
        <p>These terms may change; the effective date below reflects the current version.</p>

        <h2>Governing law and contact</h2>
        <p>
          White Oak Operations
          <br />
          17 Ridgeway Drive, Cataula, GA 31804
          <br />
          <a href="tel:+17063661096">(706) 366-1096</a> &middot;{" "}
          <a href="mailto:jacobstarling4313@gmail.com">
            jacobstarling4313@gmail.com
          </a>
        </p>
        <p className="owner-todo">
          Owner/counsel action still needed: legal entity type, formation
          state, and registered agent; and governing law/venue, which
          counsel must select. Selecting governing law and venue should
          weigh: the state where the business entity is formed, the
          owner&rsquo;s principal place of business, where services are
          actually performed, where clients are located, and any regulated
          industries or data types involved — not simply the state of the
          first clients.
        </p>
      </div>
    </main>
  );
}
