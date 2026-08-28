import Link from "next/link";
import Breadcrumbs from "@/components/Breadcrumbs";
import { getOffer, formatUsd, type OfferCode } from "@/lib/offers";

export default function OfferDetail({ code }: { code: OfferCode }) {
  const offer = getOffer(code);

  const serviceJsonLd = {
    "@context": "https://schema.org",
    "@type": "Service",
    name: offer.name,
    serviceType: "AI workflow consulting and implementation",
    description: offer.summary,
    offers: {
      "@type": "Offer",
      price: offer.priceUsd,
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
            <h3>Price</h3>
            <p style={{ fontSize: "1.5rem", fontFamily: "var(--font-serif)" }}>
              {formatUsd(offer.priceUsd)}
              {offer.billing === "recurring" ? "/mo" : ""}
            </p>
            <p className="hint">Deposit: {formatUsd(offer.depositUsd)}</p>
            <p className="hint">Payment schedule: {offer.paymentSchedule}</p>
          </div>
          <div className="card">
            <h3>Duration</h3>
            <p>{offer.duration}</p>
          </div>
        </div>

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
            Statement of Work precedes scheduled work; the deposit reserves
            your slot. Regulated or consequential workflows require
            additional review and may be declined.
          </p>
        </div>

        <Link href="/contact" className="btn btn-primary">
          Book a fit call
        </Link>
      </div>
    </main>
  );
}
