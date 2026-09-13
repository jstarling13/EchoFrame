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

        <h2>No warranty</h2>
        <p>
          This Site and its content are provided &ldquo;as is&rdquo; and
          &ldquo;as available,&rdquo; without warranties of any kind, express
          or implied, including implied warranties of merchantability,
          fitness for a particular purpose, and non-infringement, except to
          the extent such warranties cannot be disclaimed under applicable
          law. EchoFrame does not warrant that the Site will be
          uninterrupted, error-free, or secure.
        </p>

        <h2>Limitation of liability</h2>
        <p>
          To the maximum extent permitted by applicable law, EchoFrame will
          not be liable for any indirect, incidental, special, consequential,
          or punitive damages, or any loss of profits, revenue, data, or
          goodwill, arising from your use of this Site, even if advised of
          the possibility of such damages. To the maximum extent permitted
          by applicable law, EchoFrame&rsquo;s total liability arising from
          or relating to this Site is limited to $100. This limitation
          applies regardless of the legal theory on which liability is
          based, and does not apply where it cannot be limited under
          applicable law. This section governs use of the Site only &mdash;
          liability arising from an actual paid engagement is instead
          governed by the limitation-of-liability provision in the signed
          Master Services Agreement or Statement of Work for that
          engagement, not this page.
        </p>

        <h2>Changes</h2>
        <p>These terms may change; the effective date above reflects the current version.</p>

        <h2>Governing law and venue</h2>
        <p>
          These Terms are governed by the laws of the State of Georgia,
          without regard to its conflict-of-laws principles. Any dispute
          arising from your use of this Site that is not otherwise resolved
          is subject to the exclusive jurisdiction of the state and federal
          courts located in Georgia.
        </p>

        <h2>Contact</h2>
        <p>
          EchoFrame (Jacob Starling)
          <br />
          Columbus, Georgia area
          <br />
          <a href="tel:+17063661096">(706) 366-1096</a> &middot;{" "}
          <a href="mailto:jacob.starling@echoframe.net">
            jacob.starling@echoframe.net
          </a>
        </p>
      </div>
    </main>
  );
}
