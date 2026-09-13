import type { Metadata } from "next";
import Breadcrumbs from "@/components/Breadcrumbs";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Privacy policy for the EchoFrame website.",
  robots: { index: false, follow: true },
};

export default function PrivacyPage() {
  return (
    <main id="content">
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/privacy", label: "Privacy" }]} />
        <h1>Privacy Policy</h1>
        <p className="hint">Effective date: September 13, 2026</p>
        <p>
          This Privacy Policy describes how EchoFrame collects and uses
          information through this website, echoframe.net (the
          &ldquo;Site&rdquo;). EchoFrame is operated by Jacob Starling, doing
          business as EchoFrame (&ldquo;EchoFrame,&rdquo; &ldquo;we,&rdquo;
          or &ldquo;us&rdquo;).
        </p>

        <h2>Scope: this Site, not client engagements</h2>
        <p>
          This policy covers only the information collected through this
          public marketing website &mdash; for example, when you submit the
          contact form. It does not cover information exchanged as part of
          an actual paid engagement, which may include financial records,
          employee information, system credentials, API data, or internal
          business documents. That information is governed by the signed
          Master Services Agreement, Statement of Work, and/or Data
          Processing Agreement for that engagement, not this policy.
        </p>

        <h2>Information we collect</h2>
        <p>When you submit the contact form on this Site, EchoFrame collects:</p>
        <ul>
          <li>Your name and work email address</li>
          <li>Company name and your role</li>
          <li>Company website (optional)</li>
          <li>Approximate number of employees</li>
          <li>State or region</li>
          <li>A description of the workflow or problem you're describing</li>
          <li>How urgent the request is</li>
          <li>How you heard about EchoFrame (optional)</li>
          <li>Your consent confirmation</li>
        </ul>
        <p>
          Standard technical information &mdash; such as your IP address,
          browser type, and general device information &mdash; is also
          logged automatically by the Site's hosting infrastructure, as it
          is for any website, for security and abuse-prevention purposes.
        </p>
        <p>
          EchoFrame does not collect payment information, financial account
          numbers, health information, or government ID numbers through this
          Site.
        </p>

        <h2>How we use it</h2>
        <p>
          EchoFrame uses the information you submit to respond to your
          inquiry, evaluate whether your project is a good fit, and keep a
          record of the request. Technical log data is used to operate,
          secure, and troubleshoot the Site.
        </p>

        <h2>Service providers</h2>
        <p>
          <strong>Vercel</strong> (website hosting and infrastructure) is
          currently the only third party involved in operating this Site.
          EchoFrame does not currently use a third-party CRM, email-delivery
          service, rate-limiting/abuse-prevention service, marketing
          platform, or advertising network in connection with this Site. If
          that changes, this section will be updated to name the new
          provider before it begins processing your information.
        </p>

        <h2>AI use</h2>
        <p>
          Your contact form submission is not processed by any automated AI
          system as part of receiving or routing it &mdash; a person (Jacob
          Starling) reads and responds to inquiries directly. EchoFrame does
          not paste your name, email, company, or the details of your
          inquiry into general-purpose AI tools (such as Claude or ChatGPT).
          Jacob may use those tools separately, on his own, for generic
          drafting help that does not include your specific submitted
          information. If EchoFrame begins using an AI system to process,
          score, or route website inquiries &mdash; or begins including
          submitted information in prompts to a third-party AI tool &mdash;
          this section will be updated, and that tool will be named as a
          service provider above, before that use begins. AI tools used
          during an actual client engagement are addressed separately in the
          applicable Statement of Work, not this policy.
        </p>

        <h2>Cookies and tracking</h2>
        <p>
          This Site does not currently use advertising or cross-site
          tracking cookies, and does not currently run Google Analytics,
          Meta/Facebook Pixel, LinkedIn Insight Tag, Calendly, reCAPTCHA, or
          comparable third-party tracking tools. If analytics or a similar
          tool is added in the future, this section will be updated to
          disclose it, along with any consent mechanism required for your
          jurisdiction, before it is activated.
        </p>
        <p>
          Because EchoFrame does not engage in cross-site behavioral
          tracking through the Site, browser &ldquo;Do Not Track&rdquo;
          signals do not change the Site&rsquo;s behavior. EchoFrame does not
          permit third parties to collect personally identifiable
          information through the Site about visitors&rsquo; activities over
          time and across unrelated websites for behavioral advertising
          purposes, and does not sell or share personal information in a way
          that a Global Privacy Control signal would opt you out of.
        </p>

        <h2>Sharing, sale, and advertising</h2>
        <p>
          EchoFrame does not sell your personal information and does not
          share it with third parties for their own independent marketing
          or advertising purposes. EchoFrame does not use your information
          for targeted or cross-context behavioral advertising. Information
          may be disclosed if required by law, subpoena, or valid legal
          process, or to protect the rights, property, or safety of
          EchoFrame, its clients, or others.
        </p>

        <h2>Retention</h2>
        <p>
          Contact form submissions and related correspondence are ordinarily
          retained for up to 24 months from the date of submission. EchoFrame
          may retain information longer than 24 months, or decline to delete
          it on request, where reasonably necessary for legal obligations,
          security, fraud prevention, dispute resolution, the establishment
          or defense of legal claims, or another lawful purpose.
          Technical/security logs are retained for a shorter period
          consistent with standard hosting-provider practice. If you engage
          EchoFrame for a paid project, records related to that engagement
          are retained per the signed agreement and applicable recordkeeping
          requirements, not this policy.
        </p>

        <h2>Your privacy rights</h2>
        <p>
          Depending on where you're located, you may have rights under
          applicable law to request access to the personal information
          EchoFrame holds about you, request correction of inaccurate
          information, request deletion, and opt out of marketing
          communications. To exercise any of these rights, contact
          EchoFrame using the information below. EchoFrame may ask for
          information to verify your identity before fulfilling a request,
          and will respond within the period required by applicable law.
        </p>

        <h2>Security</h2>
        <p>
          EchoFrame uses reasonable technical and organizational safeguards
          designed to protect the information submitted through this Site,
          including encrypted transmission (HTTPS) and access controls on
          hosting infrastructure. No method of transmission or storage is
          completely secure, and EchoFrame cannot guarantee absolute
          security.
        </p>

        <h2>Children's privacy</h2>
        <p>
          This Site is directed to business owners and professionals, not
          children. EchoFrame does not knowingly collect personal
          information from anyone under 18. If you believe a child has
          provided information through this Site, contact EchoFrame below
          and it will be deleted.
        </p>

        <h2>Changes to this policy</h2>
        <p>
          EchoFrame may update this policy as its practices, vendors, or
          legal obligations change. Material changes will be reflected by
          updating the effective date above.
        </p>

        <h2>Contact</h2>
        <p>
          EchoFrame (Jacob Starling)
          <br />
          <a href="tel:+17063661096">(706) 366-1096</a>
          <br />
          <a href="mailto:jacob.starling@echoframe.net">
            jacob.starling@echoframe.net
          </a>
        </p>
      </div>
    </main>
  );
}
