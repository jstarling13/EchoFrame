import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import EngagementJourney from "@/components/EngagementJourney";
import {
  getOffer,
  formatUsd,
  getDisplayPriceUsd,
  getDueAtCheckoutUsd,
  getInvoiceMilestones,
  type OfferCode,
} from "@/lib/offers";

export default function OfferDetail({ code }: { code: OfferCode }) {
  const offer = getOffer(code);
  const invoiceMilestones = getInvoiceMilestones(offer);

  const serviceJsonLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: offer.name,
    serviceType: "AI workflow consulting and implementation",
    description: offer.summary,
    offers: {
      "@type": "Offer",
      price: getDisplayPriceUsd(offer),
      priceCurrency: "USD",
      availability: "https://schema.org/InStock",
    },
  };

  return (
    <main id="content">
      {/* Service structured data uses only approved v1 commercial facts
          (name, price) — see strategy/DECISION_LOG.md. No fabricated
          ratings, locations, or testimonials are added. */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceJsonLd) }}
      />
      <div className="container section">
        <Breadcrumbs trail={[{ href: "/services", label: "Services" }, { href: `/${offer.slug}`, label: offer.name }]} />
        <p className="eyebrow">{offer.code}</p>
        <h1>{offer.name}</h1>
        <p>{offer.summary}</p>

        <div className="grid grid-2" style={{ margin: "2rem 0" }}>
          <div className="card">
            <h3>Total contract price</h3>
            <p style={{ fontSize: "1.5rem", fontFamily: "var(--font-serif)" }}>
              {formatUsd(getDisplayPriceUsd(offer))}
              {offer.billing === "recurring" ? "/mo" : ""}
            </p>
            <p className="hint">
              Initial payment: {formatUsd(getDueAtCheckoutUsd(offer))}{" "}
              (invoiced privately after a signed SOW — not a public
              checkout)
            </p>
            <p className="hint">Payment schedule: {offer.paymentSchedule}</p>
            {offer.billing === "recurring" && offer.initialTermMonths && (
              <p className="hint">
                {offer.initialTermMonths}-month initial contractual term
                {offer.initialTermTotalUsd
                  ? ` (${formatUsd(offer.initialTermTotalUsd)} minimum commitment)`
                  : ""}
                . See <Link href="/support#term">initial-term terms</Link>.
              </p>
            )}
          </div>
          <div className="card">
            <h3>Duration</h3>
            <p>{offer.duration}</p>
          </div>
        </div>

        {invoiceMilestones.length > 0 && (
          <>
            <h2>Payment milestones after the deposit</h2>
            <p className="hint" style={{ marginBottom: "1rem" }}>
              Billed separately by invoice against the signed Statement of
              Work as each milestone is reached — not charged today.
            </p>
            <div className="offers-table-wrap" style={{ marginBottom: "2rem" }}>
              <table className="offers">
                <thead>
                  <tr>
                    <th scope="col">Milestone</th>
                    <th scope="col">Amount</th>
                    <th scope="col">Due</th>
                  </tr>
                </thead>
                <tbody>
                  {invoiceMilestones.map((m) => (
                    <tr key={m.id}>
                      <td>{m.label}</td>
                      <td>{formatUsd(m.amountUsd)}</td>
                      <td>{m.trigger}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        <h2>Deliverables</h2>
        <ul>
          {offer.deliverables.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>

        <h2>Exclusions</h2>
        <ul>
          {offer.exclusions.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>

        <div className="callout callout-risk" style={{ margin: "2rem 0" }}>
          <p>
            USD pricing before sales tax. Third-party software and approved
            travel are separate unless the SOW says otherwise. A signed
            Statement of Work precedes scheduled work; the initial payment,
            invoiced privately after that SOW is signed, reserves your
            slot but is not the full contract price for multi-milestone
            offers. Regulated or consequential workflows require
            additional review and may be declined.
          </p>
        </div>

        <EngagementJourney />

        <Link href="/contact" className="btn btn-primary">
          Book a fit call
        </Link>
      </div>
    </main>
  );
}
