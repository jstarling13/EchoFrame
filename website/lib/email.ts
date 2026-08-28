/**
 * Transactional email via the Resend REST API (chosen as a reference
 * implementation because EMAIL_PROVIDER_API_KEY / EMAIL_FROM already match
 * its shape). Vendor selection is an open owner decision
 * (strategy/OPEN_QUESTIONS.md) — swap this file if a different provider is
 * chosen. No SDK dependency is required; this is a single fetch call.
 */

interface SendEmailInput {
  to: string;
  subject: string;
  text: string;
}

export async function sendNotificationEmail(
  input: SendEmailInput
): Promise<{ sent: boolean; reason?: string }> {
  const apiKey = process.env.EMAIL_PROVIDER_API_KEY;
  const from = process.env.EMAIL_FROM;

  if (!apiKey || !from) {
    console.warn("email_not_configured", { to: input.to });
    return { sent: false, reason: "not_configured" };
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: input.to,
      subject: input.subject,
      text: input.text,
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    console.error("email_send_failed", res.status);
    return { sent: false, reason: `provider_status_${res.status}` };
  }

  return { sent: true };
}
