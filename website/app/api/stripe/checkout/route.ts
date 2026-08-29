import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getStripeClient } from "@/lib/stripe";
import { getOffer, getCheckoutMilestone, type OfferCode } from "@/lib/offers";

export const runtime = "nodejs";

/**
 * Creates a Stripe-hosted Checkout Session for the SINGLE "checkout"
 * milestone of an offer (the deposit for O2-O4, the full amount for O1,
 * or one month for O5) and redirects the browser there. No Stripe.js is
 * loaded client-side.
 *
 * This route NEVER accepts a client-supplied amount. The only
 * client-supplied input is `offerCode`; the amount actually charged is
 * fully determined server-side by lib/offers.ts (which milestone has
 * method "checkout") and the Stripe Price ID configured for it in the
 * environment. Later invoice milestones (blueprint, acceptance, handoff,
 * O2/O3/O4 final payment) are never reachable through this route — those
 * are billed by staff via a Stripe Invoice against the signed SOW.
 *
 * Payment success alone never authorizes project work — see
 * STRIPE_SPECIFICATION.md "Entitlement/status": the signed SOW and
 * internal project record remain authoritative for scope.
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

  let milestone: ReturnType<typeof getCheckoutMilestone>;
  try {
    milestone = getCheckoutMilestone(offer);
  } catch (err) {
    // Malformed offer data (not exactly one checkout milestone). Fail
    // closed rather than guess which amount to charge.
    console.error("offer_checkout_milestone_invalid", offer.code, err);
    return NextResponse.json(
      { ok: false, error: "This offer is not available for online checkout right now." },
      { status: 503 }
    );
  }

  const priceId = process.env[offer.stripeCheckoutPriceEnvVar];
  if (!priceId) {
    console.error(
      "stripe_price_not_configured",
      offer.code,
      offer.stripeCheckoutPriceEnvVar
    );
    return NextResponse.json(
      { ok: false, error: "This offer is not yet configured for online checkout. Contact us to proceed." },
      { status: 503 }
    );
  }

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || req.nextUrl.origin;

  const sharedMetadata = {
    offer_code: offer.code,
    milestone_id: milestone.id,
    project_id: parsed.data.projectId || "",
    client_id: parsed.data.clientId || "",
    environment: process.env.VERCEL_ENV || process.env.NODE_ENV || "development",
    source: "website_checkout",
  };

  try {
    const stripe = getStripeClient();
    const session = await stripe.checkout.sessions.create({
      mode: offer.billing === "recurring" ? "subscription" : "payment",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${siteUrl}/thank-you?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}/services?checkout=cancelled`,
      billing_address_collection: "required",
      metadata: sharedMetadata,
      // Also stamp metadata onto the Subscription itself (not just the
      // Checkout Session), because subscription lifecycle webhook events
      // (created/updated/deleted, used for O5 initial-term tracking —
      // see lib/subscription-term.ts) carry the Subscription object, which
      // does not otherwise inherit Checkout Session metadata.
      ...(offer.billing === "recurring"
        ? { subscription_data: { metadata: sharedMetadata } }
        : {}),
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
