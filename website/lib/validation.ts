import { z } from "zod";

/**
 * Fit-call lead form. Fields match WEBSITE_SPECIFICATION.md "Forms" section
 * exactly. Never add fields that collect sensitive data (health, financial
 * account, credential, or privileged information) per site copy and
 * CLIENT_DATA_POLICY.md.
 */
export const employeeRanges = [
  "1-9",
  "10-24",
  "25-49",
  "50-99",
  "100-250",
  "250+",
] as const;

export const urgencyLevels = ["Exploring", "This quarter", "Urgent"] as const;

// Matches the three buyer personas in strategy/ICP_PERSONAS_AND_TRIGGERS.md,
// plus a catch-all for anyone who doesn't fit those.
export const roles = [
  "Owner / Managing Partner",
  "Office / Operations Manager",
  "Bookkeeper / CPA / Finance Professional",
  "Other",
] as const;

export const usStates = [
  "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
  "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
  "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
  "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
  "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
  "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
  "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
  "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
  "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
  "Outside the U.S.",
] as const;

export const contactFormSchema = z.object({
  name: z.string().trim().min(2, "Enter your full name").max(120),
  email: z.string().trim().email("Enter a valid work email").max(200),
  company: z.string().trim().min(2, "Enter your company name").max(160),
  role: z.enum(roles, { message: "Select a role" }),
  website: z
    .string()
    .trim()
    .url("Enter a full URL, including https://")
    .max(200)
    .optional()
    .or(z.literal("")),
  employeeRange: z.enum(employeeRanges, {
    message: "Select an employee range",
  }),
  state: z.enum(usStates, { message: "Select a state" }),
  workflowProblem: z
    .string()
    .trim()
    .min(20, "Describe the workflow in at least 20 characters")
    .max(2000, "Keep this under 2000 characters"),
  urgency: z.enum(urgencyLevels, { message: "Select an urgency level" }),
  referralSource: z.string().trim().max(160).optional().or(z.literal("")),
  consent: z.literal(true, {
    message: "Consent is required to submit this form",
  }),
});

/**
 * Honeypot field name is intentionally NOT part of the zod schema: a
 * dynamic (env-driven) property key on a zod object collapses every other
 * field's inferred type to a union including that key's type. The route
 * handler reads this field directly off the raw parsed JSON body, before
 * zod validation, using this same name.
 */
export function getHoneypotFieldName(): string {
  return process.env.CONTACT_FORM_HONEYPOT_FIELD || "company_website";
}

/** True if the honeypot field on the raw request body was filled in — i.e. a bot. */
export function isHoneypotFilled(raw: unknown): boolean {
  if (!raw || typeof raw !== "object") return false;
  const value = (raw as Record<string, unknown>)[getHoneypotFieldName()];
  return typeof value === "string" && value.length > 0;
}

export type ContactFormInput = z.infer<typeof contactFormSchema>;

const STRING_FIELDS = [
  "name",
  "email",
  "company",
  "role",
  "website",
  "employeeRange",
  "state",
  "workflowProblem",
  "urgency",
  "referralSource",
] as const;

/**
 * The browser form always posts every field as a string (LeadForm.tsx uses
 * `String(data.get(...) || "")`), so a missing key only happens on a raw
 * API call. Normalize missing/non-string values to "" so validation always
 * hits the friendly `.min()`/`.enum()` messages above instead of zod's
 * generic "expected string, received undefined" type error.
 */
export function normalizeContactPayload(raw: unknown): Record<string, unknown> {
  const input = raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  const normalized: Record<string, unknown> = { ...input };
  for (const field of STRING_FIELDS) {
    if (typeof normalized[field] !== "string") normalized[field] = "";
  }
  normalized.consent = normalized.consent === true;
  return normalized;
}

export function flattenZodErrors(
  error: z.ZodError
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = issue.path.join(".") || "form";
    if (!out[key]) out[key] = issue.message;
  }
  return out;
}
