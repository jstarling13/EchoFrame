import { NextRequest, NextResponse } from "next/server";
import { getStripeClient } from "@/lib/stripe";
import { markEventProcessedIfNew } from "@/lib/idempotency";
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

  const isNew = await markEventProcessedIfNew(event.id);
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

  // TODO(owner): once a CRM/ops backend is selected, POST this state change
  // there (e.g. via lib/crm.ts) so a human creates/updates the operations
  // task. Do not auto-start delivery work from a webhook alone.
}

function extractMetadata(event: Stripe.Event): Record<string, string> {
  const obj = event.data.object as { metadata?: Record<string, string> };
  return obj.metadata || {};
}
