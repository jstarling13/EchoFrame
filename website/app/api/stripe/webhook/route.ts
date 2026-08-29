import { NextRequest, NextResponse } from "next/server";
import { getStripeClient } from "@/lib/stripe";
import { markEventProcessedIfNew } from "@/lib/idempotency";
import { getOffer, type OfferCode } from "@/lib/offers";
import { checkEarlyCancellation } from "@/lib/subscription-term";
import type Stripe from "stripe";

export const runtime = "nodejs";

/**
 * Verifies the raw request body against the Stripe signature, deduplicates
 * by event ID, and updates payment state / creates an operations task.
 * Never authorizes risky work automatically — payment status only.
 * Handles the event set from STRIPE_SPECIFICATION.md "Webhooks".
 */
const HANDLED_EVENTS = new Set([
  "checkout.session.completed",
  "checkout.session.async_payment_succeeded",
  "checkout.session.async_payment_failed",
  "payment_intent.succeeded",
  "payment_intent.payment_failed",
  "invoice.paid",
  "invoice.payment_failed",
  "invoice.overdue",
  "invoice.voided",
  "customer.subscription.created",
  "customer.subscription.updated",
  "customer.subscription.deleted",
  "charge.refunded",
  "charge.dispute.created",
  "charge.dispute.closed",
]);

export async function POST(req: NextRequest) {
  const signature = req.headers.get("stripe-signature");
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !webhookSecret) {
    console.error("stripe_webhook_misconfigured");
    return NextResponse.json({ ok: false }, { status: 500 });
  }

  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    const stripe = getStripeClient();
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (err) {
    console.error("stripe_webhook_invalid_signature", err);
    return NextResponse.json({ ok: false, error: "Invalid signature" }, { status: 400 });
  }

  let isNew: boolean;
  try {
    isNew = await markEventProcessedIfNew(event.id);
  } catch (err) {
    // Fail closed: without durable idempotency we cannot safely guarantee
    // this event won't be double-processed across serverless instances.
    // Return 500 so Stripe retries once the durable store is configured
    // or reachable again — never process the event without it.
    console.error("stripe_webhook_idempotency_unavailable", event.id, err);
    return NextResponse.json(
      { ok: false, error: "Idempotency store unavailable; configuration required." },
      { status: 500 }
    );
  }

  if (!isNew) {
    // Duplicate delivery: acknowledge without reprocessing.
    return NextResponse.json({ ok: true, duplicate: true }, { status: 200 });
  }

  if (!HANDLED_EVENTS.has(event.type)) {
    // Acknowledge quickly; nothing to do for event types outside our matrix.
    return NextResponse.json({ ok: true, ignored: true }, { status: 200 });
  }

  try {
    await recordPaymentStateChange(event);
  } catch (err) {
    // Retry-safe: return 500 so Stripe retries; idempotency guard above
    // prevents duplicate side effects on the retry once this succeeds.
    console.error("stripe_webhook_handler_error", event.type, err);
    return NextResponse.json({ ok: false }, { status: 500 });
  }

  return NextResponse.json({ ok: true }, { status: 200 });
}

async function recordPaymentStateChange(event: Stripe.Event): Promise<void> {
  // This app has no database yet. Log a structured, non-sensitive summary so
  // the event is auditable, and this is the integration point for creating
  // an operations task in the chosen CRM/ops system (operations/CRM_AND_FOLDER_SPEC.md).
  // No card data, secrets, or free-text workflow content is ever logged here.
  const metadata = extractMetadata(event);
  console.info("stripe_payment_state_change", {
    eventId: event.id,
    type: event.type,
    offerCode: metadata.offer_code,
    projectId: metadata.project_id,
    clientId: metadata.client_id,
  });

  if (event.type === "customer.subscription.updated") {
    checkForEarlyCancellationRequest(event);
  }
  if (event.type === "customer.subscription.deleted") {
    checkForEarlyCancellationCompletion(event);
  }

  // TODO(owner): once a CRM/ops backend is selected, POST this state change
  // there (e.g. via lib/crm.ts) so a human creates/updates the operations
  // task. Do not auto-start delivery work from a webhook alone.
}

/**
 * O5's 3-month initial term is a CONTRACTUAL commitment (see
 * strategy/DECISION_LOG.md and lib/subscription-term.ts) — Stripe does not
 * enforce it technically, and this handler never blocks or auto-charges
 * anything. It only flags, in logs, when a cancellation was requested (or
 * completed) before the initial term elapsed, so a human follows up per
 * the signed SOW/MSA. Final cancellation/early-termination wording is
 * pending attorney review (see website/docs/O5_INITIAL_TERM.md).
 */
function checkForEarlyCancellationRequest(event: Stripe.Event): void {
  const subscription = event.data.object as Stripe.Subscription;
  const previous = (
    event.data as { previous_attributes?: Partial<Stripe.Subscription> }
  ).previous_attributes;

  const justRequestedCancellation =
    subscription.cancel_at_period_end === true &&
    previous?.cancel_at_period_end !== true;

  if (!justRequestedCancellation) return;

  flagIfWithinInitialTerm(subscription, subscription.canceled_at ?? nowEpochSeconds());
}

function checkForEarlyCancellationCompletion(event: Stripe.Event): void {
  const subscription = event.data.object as Stripe.Subscription;
  flagIfWithinInitialTerm(
    subscription,
    subscription.ended_at ?? subscription.canceled_at ?? nowEpochSeconds()
  );
}

function flagIfWithinInitialTerm(
  subscription: Stripe.Subscription,
  cancellationEpochSeconds: number
): void {
  const offerCode = subscription.metadata?.offer_code as OfferCode | undefined;
  if (!offerCode) {
    console.warn(
      "stripe_subscription_missing_offer_metadata",
      subscription.id,
      "cannot check initial-term status"
    );
    return;
  }

  const offer = getOffer(offerCode);
  if (!offer.initialTermMonths) return; // offer has no minimum term

  const startEpochSeconds = subscription.start_date ?? subscription.created;
  const result = checkEarlyCancellation(
    startEpochSeconds,
    cancellationEpochSeconds,
    offer.initialTermMonths
  );

  if (result.isWithinInitialTerm) {
    // Flag only — never auto-charge or block. A human resolves this per
    // the signed contract's early-termination terms.
    console.warn("stripe_subscription_cancelled_within_initial_term", {
      subscriptionId: subscription.id,
      offerCode,
      projectId: subscription.metadata?.project_id,
      monthsElapsed: Number(result.monthsElapsed.toFixed(2)),
      initialTermMonths: result.initialTermMonths,
    });
  }
}

function nowEpochSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

function extractMetadata(event: Stripe.Event): Record<string, string> {
  const obj = event.data.object as { metadata?: Record<string, string> };
  return obj.metadata || {};
}
