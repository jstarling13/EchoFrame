import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "node:crypto";
import {
  contactFormSchema,
  flattenZodErrors,
  isHoneypotFilled,
  normalizeContactPayload,
} from "@/lib/validation";
import { checkRateLimit } from "@/lib/rate-limit";
import { routeLeadToCrm } from "@/lib/crm";
import { sendNotificationEmail } from "@/lib/email";
import {
  resolveSubmissionOutcome,
  shouldReturnServiceUnavailable,
} from "@/lib/lead-routing";
import { isProductionRuntime } from "@/lib/durable-store";

export const runtime = "nodejs";

function getClientIdentifier(req: NextRequest): string {
  const forwarded = req.headers.get("x-forwarded-for");
  return forwarded?.split(",")[0]?.trim() || "unknown";
}

export async function POST(req: NextRequest) {
  const identifier = getClientIdentifier(req);

  const { success: withinLimit } = await checkRateLimit(identifier);
  if (!withinLimit) {
    return NextResponse.json(
      { ok: false, errors: { form: "Too many requests. Try again in a minute." } },
      { status: 429 }
    );
  }

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return NextResponse.json(
      { ok: false, errors: { form: "Invalid request body." } },
      { status: 400 }
    );
  }

  const leadId = randomUUID();
  const honeypotFilled = isHoneypotFilled(raw);

  if (honeypotFilled) {
    // Silently succeed to avoid tipping off bots; nothing is routed or attempted.
    console.info("contact_form_submission_outcome", { leadId, outcome: "spam" });
    return NextResponse.json({ ok: true, leadId }, { status: 200 });
  }

  const parsed = contactFormSchema.safeParse(normalizeContactPayload(raw));
  if (!parsed.success) {
    return NextResponse.json(
      { ok: false, errors: flattenZodErrors(parsed.error) },
      { status: 400 }
    );
  }

  const crmConfigured = Boolean(process.env.CRM_WEBHOOK_URL);
  const emailConfigured = Boolean(
    process.env.EMAIL_PROVIDER_API_KEY &&
      process.env.EMAIL_FROM &&
      process.env.LEAD_NOTIFICATION_EMAIL
  );

  const submittedAt = new Date().toISOString();

  const [crmResult, emailResult] = await Promise.all([
    routeLeadToCrm({
      name: parsed.data.name,
      email: parsed.data.email,
      company: parsed.data.company,
      role: parsed.data.role,
      website: parsed.data.website || null,
      employeeRange: parsed.data.employeeRange,
      state: parsed.data.state,
      workflowProblem: parsed.data.workflowProblem,
      urgency: parsed.data.urgency,
      referralSource: parsed.data.referralSource || null,
      consent: parsed.data.consent,
      source: "website_fit_call_form",
      submittedAt,
      leadId,
    }),
    (async () => {
      if (!emailConfigured) return { sent: false, reason: "not_configured" as const };
      return sendNotificationEmail({
        to: process.env.LEAD_NOTIFICATION_EMAIL!,
        subject: `New discovery call request: ${parsed.data.company}`,
        text: [
          `Lead ID: ${leadId}`,
          `Name: ${parsed.data.name}`,
          `Email: ${parsed.data.email}`,
          `Company: ${parsed.data.company}`,
          `Role: ${parsed.data.role}`,
          `Employees: ${parsed.data.employeeRange}`,
          `State: ${parsed.data.state}`,
          `Urgency: ${parsed.data.urgency}`,
          `Referral source: ${parsed.data.referralSource || "n/a"}`,
          `Workflow: ${parsed.data.workflowProblem}`,
        ].join("\n"),
      });
    })(),
  ]);

  const outcome = resolveSubmissionOutcome({
    isHoneypotFilled: false,
    crmConfigured,
    emailConfigured,
    crmDelivered: crmResult.delivered,
    emailSent: emailResult.sent,
  });

  // Never log free-text form content (workflowProblem); log only routing
  // outcomes for observability, per WEBSITE_SPECIFICATION.md "logging
  // without sensitive form bodies".
  console.info("contact_form_submission_outcome", {
    leadId,
    outcome,
    crmConfigured,
    emailConfigured,
    crmDelivered: crmResult.delivered,
    emailSent: emailResult.sent,
  });

  if (shouldReturnServiceUnavailable(outcome, isProductionRuntime())) {
    // Both configured destinations failed (or none is configured at all)
    // in a production environment: do not present a normal success state
    // — the lead would otherwise silently vanish.
    console.error("contact_form_no_lead_destination_available", { leadId, outcome });
    return NextResponse.json(
      {
        ok: false,
        errors: {
          form: "We couldn't process your request right now. Please try again shortly or reach out directly.",
        },
      },
      { status: 503 }
    );
  }

  return NextResponse.json({ ok: true, leadId }, { status: 200 });
}
