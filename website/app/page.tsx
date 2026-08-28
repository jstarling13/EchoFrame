import Link from "next/link";
import type { Metadata } from "next";
import OfferTable from "@/components/OfferTable";

export const metadata: Metadata = {
  title: "AI Workflow Consulting, Implementation & Training",
  description:
    "Vendor-neutral AI workflow consulting for established businesses: process mapping, implementation, testing, staff training, governance, and ownership transfer.",
};

export default function Home() {
  return (
    <main>
      <section className="hero on-dark">
        <div className="container">
          <p className="eyebrow">AI operations for established businesses</p>
          <h1>Build the workflow. Train the people. Keep the capability.</h1>
          <p>
            We map the way work actually moves through your business,
            implement the right mix of AI and automation, test it, train
            your team, and transfer ownership.
          </p>
          <div className="hero-actions">
            <Link href="/contact" className="btn btn-primary">
              Book a fit call
            </Link>
            <Link href="/method" className="btn btn-secondary">
              See how the method works
            </Link>
          </div>
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <h2>Most businesses do not need another AI demo.</h2>
          <p>
            They need a repeated bottleneck fixed without losing control of
            quality, data, or judgment.
          </p>
        </div>
      </section>

      <section className="section section-alt section-border">
        <div className="container">
          <h2>What we deliver</h2>
          <ul>
            <li>Clear opportunity priorities</li>
            <li>Implemented workflows</li>
            <li>Human review and fallback</li>
            <li>Role-based training</li>
            <li>Operating documentation</li>
            <li>Honest impact measurement</li>
          </ul>
        </div>
      </section>

      <section className="section section-border">
        <div className="container">
          <h2>The OWNED Method</h2>
          <p>Observe, Weigh, Navigate, Engineer, Demonstrate and transfer.</p>
          <p>
            <Link href="/method">Read the full method</Link>
          </p>
        </div>
      </section>

      <section className="section section-alt section-border">
        <div className="container">
          <h2>Services</h2>
          <OfferTable />
          <p style={{ marginTop: "1.5rem" }}>
            Third-party software and approved travel are separate unless the
            SOW says otherwise. Regulated or consequential workflows require
            additional review and may be declined.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>Start with one workflow worth fixing.</h2>
          <Link href="/contact" className="btn btn-primary">
            Book a fit call
          </Link>
        </div>
      </section>
    </main>
  );
}
