import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Terms of Use",
  description: "Website terms of use for EchoFrame.",
  // Attorney-review draft, not final — never indexed regardless of
  // environment, even once Production is otherwise indexable.
  robots: { index: false, follow: true },
};

export default function TermsPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/terms", label: "Terms" }]} />
        <h1>Terms of Use</h1>
        <p className="hint">Effective date: September 13, 2026</p>

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
          The site and its content are owned by EchoFrame or
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
          EchoFrame
          <br />
          17 Ridgeway Drive, Cataula, GA 31804
          <br />
          <a href="tel:+17063661096">(706) 366-1096</a> &middot;{" "}
          <a href="mailto:jacob.starling@echoframe.net">
            jacob.starling@echoframe.net
          </a>
        </p>
        <p className="hint">
          EchoFrame is operated by Jacob Starling, doing business as
          EchoFrame. Governing law and venue will be specified once
          EchoFrame's legal entity is formally established.
        </p>
      </div>
    </main>
  );
}
