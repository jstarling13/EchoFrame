/**
 * Pure decision logic for what the contact API route should tell the
 * client after attempting to route a lead to the CRM and/or email.
 *
 * Explicit outcomes (per the pre-merge audit — the endpoint must not
 * present a normal success state if both destinations are unavailable):
 *
 * - "delivered": every configured destination succeeded.
 * - "partial":   at least one configured destination succeeded, at least one failed.
 * - "spam":      honeypot caught a bot; nothing was attempted. Always looks
 *                like a normal success to the client, so bots aren't tipped off.
 * - "failed":    no destination is configured, or every configured
 *                destination failed at runtime.
 */

export type RoutingOutcome = "delivered" | "partial" | "spam" | "failed";

export interface SubmissionOutcomeInput {
  isHoneypotFilled: boolean;
  crmConfigured: boolean;
  emailConfigured: boolean;
  crmDelivered: boolean;
  emailSent: boolean;
}

export function resolveSubmissionOutcome(
  input: SubmissionOutcomeInput
): RoutingOutcome {
  if (input.isHoneypotFilled) return "spam";

  const configuredCount =
    (input.crmConfigured ? 1 : 0) + (input.emailConfigured ? 1 : 0);
  if (configuredCount === 0) return "failed";

  const successCount =
    (input.crmDelivered ? 1 : 0) + (input.emailSent ? 1 : 0);
  if (successCount === configuredCount) return "delivered";
  if (successCount > 0) return "partial";
  return "failed";
}

/**
 * In production, "failed" must not be presented to the client as a normal
 * success — the route should return 503 instead. Outside production
 * (local dev/test with no CRM/email configured), keep the existing no-op
 * "success" so the form can still be exercised end-to-end without setting
 * up real destinations. "spam", "delivered", and "partial" are always a
 * normal success response, in every environment.
 */
export function shouldReturnServiceUnavailable(
  outcome: RoutingOutcome,
  isProductionRuntime: boolean
): boolean {
  return outcome === "failed" && isProductionRuntime;
}
