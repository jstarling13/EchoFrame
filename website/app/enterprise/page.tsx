import type { Metadata } from "next";
import OfferDetail from "@/components/OfferDetail";
import { getOffer } from "@/lib/offers";

const offer = getOffer("O4");

export const metadata: Metadata = {
  title: offer.name,
  description: offer.summary,
  robots: { index: false, follow: false },
};

export default function Page() {
  return <OfferDetail code="O4" />;
}
