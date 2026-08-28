/**
 * Generic CRM lead routing. Posts a signed webhook so any CRM (per
 * operations/CRM_AND_FOLDER_SPEC.md field list) can receive leads without
 * this app depending on a specific vendor SDK. CRM vendor selection is an
 * open owner decision (strategy/OPEN_QUESTIONS.md).
 */
import { createHmac } from "node:crypto";

export interface CrmLeadPayload {
  name: string;
  email: string;
  company: string;
  role: string;
  website: string | null;
  employeeRange: string;
  state: string;
  workflowProblem: string;
  urgency: string;
  referralSource: string | null;
  consent: boolean;
  source: "website_fit_call_form";
  submittedAt: string;
  leadId: string;
}

export async function routeLeadToCrm(
  lead: CrmLeadPayload
): Promise<{ delivered: boolean; reason?: string }> {
  const url = process.env.CRM_WEBHOOK_URL;
  const secret = process.env.CRM_WEBHOOK_SECRET;

  if (!url) {
    console.warn("crm_webhook_not_configured", { leadId: lead.leadId });
    return { delivered: false, reason: "not_configured" };
  }

  const body = JSON.stringify(lead);
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (secret) {
    headers["X-Signature"] = createHmac("sha256", secret).update(body).digest("hex");
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers,
      body,
      cache: "no-store",
    });
    if (!res.ok) {
      console.error("crm_webhook_failed", res.status, lead.leadId);
      return { delivered: false, reason: `status_${res.status}` };
    }
    return { delivered: true };
  } catch (err) {
    console.error("crm_webhook_unreachable", err, lead.leadId);
    return { delivered: false, reason: "unreachable" };
  }
}
