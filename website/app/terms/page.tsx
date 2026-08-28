import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Terms of Use",
  description: "Website terms of use for Practical AI Operations.",
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
            approved by New York counsel (see{" "}
            <code>legal/ATTORNEY_REVIEW_REQUIRED.md</code>). It must not be
            treated as final before that review.
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
          The site and its content are owned by Practical AI Operations or
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
        <p className="owner-todo">
          Owner/counsel action needed: legal entity name, mailing address,
          governing law/venue, and a contact route must be supplied before
          this page is published to production. Placeholder facts are
          intentionally not included.
        </p>
      </div>
    </main>
  );
}
