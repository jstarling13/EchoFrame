import Link from "next/link";
import {
  OFFERS,
  formatUsd,
  getDisplayPriceUsd,
  getDueAtCheckoutUsd,
} from "@/lib/offers";

export default function OfferTable() {
  return (
    <div className="offers-table-wrap">
      <table className="offers">
        <caption>Choose the smallest engagement that can produce evidence.</caption>
        <thead>
          <tr>
            <th scope="col">Code</th>
            <th scope="col">Offer</th>
            <th scope="col">Total contract price</th>
            <th scope="col">Initial payment</th>
            <th scope="col">Duration</th>
          </tr>
        </thead>
        <tbody>
          {OFFERS.map((offer) => (
            <tr key={offer.code}>
              <td>{offer.code}</td>
              <td>
                <Link href={`/${offer.slug}`}>{offer.name}</Link>
              </td>
              <td>
                {formatUsd(getDisplayPriceUsd(offer))}
                {offer.billing === "recurring" ? "/mo" : ""}
              </td>
              <td>{formatUsd(getDueAtCheckoutUsd(offer))}</td>
              <td>{offer.duration}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
