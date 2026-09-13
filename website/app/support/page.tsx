import type { Metadata } from "next";
import OfferDetail from "@/components/OfferDetail";
import { getOffer } from "@/lib/offers";

const offer = getOffer("O5");

export const metadata: Metadata = {
  title: offer.name,
  description: offer.summary,
  robots: { index: false, follow: false },
};

export default function Page() {
  return (
    <>
      <OfferDetail code="O5" />
      <div className="container section" id="term" style={{ paddingTop: 0 }}>
        <h2>About the 3-month initial term</h2>
        <p>
          O5 bills {"$2,500"} monthly in advance with a 3-month initial
          contractual term ({"$7,500"} minimum commitment). This term is
          set out in the signed Statement of Work — it is a contractual
          commitment, not something Stripe enforces on its own. Canceling
          the recurring payment does not by itself end the underlying
          commitment; the SOW governs what happens if service ends before
          the initial term is complete.
        </p>
        <div className="callout callout-risk">
          <p>
            Cancellation and early-termination terms are drafted but not
            yet approved by counsel (see{" "}
            <code>legal/ATTORNEY_REVIEW_REQUIRED.md</code>). This page will
            be updated with final wording once that review is complete.
          </p>
        </div>
      </div>
    </>
  );
}
