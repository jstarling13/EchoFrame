import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import ServicesGrid from "@/components/ServicesGrid";
import PricingModel from "@/components/PricingModel";
import IndustrySelector from "@/components/IndustrySelector";

export const metadata: Metadata = {
  title: "Reclaiming 42 Hours of Weekly Processing Capacity | EchoFrame",
  description:
    "EchoFrame engineers practical AI and automation for small businesses through The OWNED Method™ — bookkeeping and financial workflows, process automation, and staff training. Billed hourly, measured in outcomes.",
};

export default function Home() {
  return (
    <main>
      <section className="hero on-dark hero-photo">
        <div className="hero-media">
          <Image
            src="/images/hero-staircase.png"
            alt=""
            fill
            priority
            sizes="100vw"
          />
        </div>
        <div className="hero-overlay" />
        <div className="container">
          <p className="eyebrow">The Case for Practical AI</p>
          <h1>Reclaiming 42 Hours of Weekly Processing Capacity.</h1>
          <p>
            EchoFrame engineers hands-on AI and workflow automation for small
            businesses &mdash; delivered through The OWNED Method&trade;, a
            proprietary five-stage framework built for measurable risk
            reduction, not another platform demo. Scoped to the operation as
            it actually runs. Built to be owned outright.
          </p>
          <div className="hero-actions">
            <Link href="/contact" className="btn btn-primary">
              Request a Quote
            </Link>
            <Link href="/method" className="btn btn-secondary">
              See How the Method Works
            </Link>
          </div>
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <p className="eyebrow">Point of View</p>
          <h2>The Case for Architectural Restraint.</h2>
          <p>
            Every small business now faces the same expensive anxiety:
            pressure to "do something with AI" without an inventory of what's
            actually broken. EchoFrame's answer is restraint, not more
            platform &mdash; find the bottleneck, apply the model or workflow
            that actually fits, and prove the result before it ever scales,
            without losing control of quality, data, or judgment.
          </p>
        </div>
      </section>

      <section className="section section-alt section-border">
        <div className="container">
          <p className="eyebrow">Put the Workflow in Context</p>
          <IndustrySelector />
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <div className="callout">
            <p className="eyebrow">Proof, Not Promises</p>
            <p style={{ fontFamily: "var(--font-serif)", fontSize: "1.4rem", marginBottom: "0.75rem" }}>
              An 87.5% reduction in weekly processing time.
            </p>
            <p>
              For an anonymized multi-location food-service accounting
              operation, EchoFrame reduced a client-tracked weekly process
              from approximately 48 hours to approximately six hours,
              reclaiming roughly 42 hours of weekly capacity. The result was
              observed from June through September 2026, was not
              independently audited, and should not be interpreted as
              guaranteed savings or a typical result.
            </p>
            <p style={{ marginTop: "0.75rem" }}>
              <Link href="/insights/from-three-16-hour-days-to-six-hours-a-week">
                Read the full case study &rarr;
              </Link>
            </p>
          </div>
        </div>
      </section>

      <section className="section section-border">
        <div className="container grid grid-3">
          <div>
            <Image
              className="line-icon on-light"
              src="/images/icon-discovery.png"
              alt=""
              width={48}
              height={48}
            />
            <h3>Consulting</h3>
            <p>Map how the work actually moves before touching any tool.</p>
          </div>
          <div>
            <Image
              className="line-icon on-light"
              src="/images/icon-implementation.png"
              alt=""
              width={48}
              height={48}
            />
            <h3>Implementation</h3>
            <p>Build, test, and integrate the workflow into daily operations.</p>
          </div>
          <div>
            <Image
              className="line-icon on-light"
              src="/images/icon-training.png"
              alt=""
              width={48}
              height={48}
            />
            <h3>Training</h3>
            <p>Hand the team the skills and documentation to run it alone.</p>
          </div>
        </div>
      </section>

      <section className="section section-alt section-border">
        <div className="container">
          <h2>What EchoFrame Delivers</h2>
          <ul>
            <li>Clear opportunity priorities</li>
            <li>Implemented workflows</li>
            <li>Human review and fallback</li>
            <li>Role-based training</li>
            <li>Operating documentation</li>
            <li>Measurable risk reduction</li>
          </ul>
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <h2>The OWNED Method&trade;</h2>
          <p>Observe, Weigh, Navigate, Engineer, Demonstrate and Transfer.</p>
          <p>
            <Link href="/method">Read the Full Method</Link>
          </p>
        </div>
      </section>

      <section className="section section-alt section-border">
        <div className="container">
          <h2>One Engagement Model. Every Capability the Business Needs.</h2>
          <p>
            A single hourly rate covers all of it &mdash; scoped to the
            problem in front of it, not sold off a shelf of fixed packages.
          </p>
          <ServicesGrid />
          <p style={{ marginTop: "2rem" }}>
            <Link href="/services">See Pricing and Every Service in Detail &rarr;</Link>
          </p>
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <h2>How Engagement Works</h2>
          <PricingModel />
          <p className="hint" style={{ marginTop: "1rem" }}>
            No enterprise price tag and no fixed packages &mdash; an hourly
            rate, a travel fee for onsite work, and a modest daily food
            stipend when it runs a full day on-site.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>Start With the Workflow Costing You the Most.</h2>
          <Link href="/contact" className="btn btn-primary">
            Request a Quote
          </Link>
        </div>
      </section>
    </main>
  );
}
