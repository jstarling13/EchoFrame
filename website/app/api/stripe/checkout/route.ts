import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getStripeClient } from "@/lib/stripe";
import { getOffer, type OfferCode } from "@/lib/offers";

export const runtime = "nodejs";

/**
 * Creates a Stripe-hosted Checkout Session for a deposit/prepaid offer
 * (O1-O4 one-time, O5 recurring) and redirects the browser there. No
 * Stripe.js is loaded client-side. Payment success alone never authorizes
 * project work — see STRIPE_SPECIFICATION.md "Entitlement/status": the
 * signed SOW and internal project record remain authoritative for scope.
 */
const requestSchema = z.object({
  offerCode: z.enum(["O1", "O2", "O3", "O4", "O5"]),
  projectId: z.string().trim().max(60).optional(),
  clientId: z.string().trim().max(60).optional(),
});

export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid request body." }, { status: 400 });
  }

  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: "Invalid offer code." }, { status: 400 });
  }

  const offer = getOffer(parsed.data.offerCode as OfferCode);
  const priceId = process.env[offer.stripePriceEnvVar];
  if (!priceId) {
    console.error("stripe_price_not_configured", offer.code, offer.stripePriceEnvVar);
    return NextResponse.json(
      { ok: false, error: "This offer is not yet configured for online checkout. Contact us to proceed." },
      { status: 503 }
    );
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || req.nextUrl.origin;

  try {
    const stripe = getStripeClient();
    const session = await stripe.checkout.sessions.create({
      mode: offer.billing === "recurring" ? "subscription" : "payment",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${siteUrl}/thank-you?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/services?checkout=cancelled`,
      billing_address_collection: "required",
      metadata: {
        offer_code: offer.code,
        project_id: parsed.data.projectId || "",
        client_id: parsed.data.clientId || "",
        environment: process.env.NODE_ENV || "development",
        source: "website_checkout",
      },
    });

    if (!session.url) {
      return NextResponse.json({ ok: false, error: "Could not start checkout." }, { status: 502 });
    }

    return NextResponse.redirect(session.url, { status: 303 });
  } catch (err) {
    console.error("stripe_checkout_create_failed", err);
    return NextResponse.json({ ok: false, error: "Could not start checkout." }, { status: 502 });
  }
}
