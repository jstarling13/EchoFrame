import { describe, expect, it } from "vitest";
import {
  contactFormSchema,
  getHoneypotFieldName,
  isHoneypotFilled,
  normalizeContactPayload,
} from "../lib/validation";

const validPayload = {
  name: "Jordan Lee",
  email: "jordan@example.com",
  company: "Example Co",
  role: "Office / Operations Manager" as const,
  website: "https://example.com",
  employeeRange: "25-49" as const,
  state: "New York" as const,
  workflowProblem: "Invoice approvals take two weeks and nobody knows why.",
  urgency: "This quarter" as const,
  referralSource: "Referral",
  consent: true as const,
  company_website: "",
};

describe("contact form validation", () => {
  it("accepts a complete, valid submission", () => {
    const result = contactFormSchema.safeParse(validPayload);
    expect(result.success).toBe(true);
  });

  it("rejects missing consent", () => {
    const result = contactFormSchema.safeParse({ ...validPayload, consent: false });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = contactFormSchema.safeParse({ ...validPayload, email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("rejects a workflow description that is too short", () => {
    const result = contactFormSchema.safeParse({ ...validPayload, workflowProblem: "too short" });
    expect(result.success).toBe(false);
  });

  it("exposes a stable honeypot field name (checked at the API route, not in this schema)", () => {
    // The honeypot key can't live inside contactFormSchema itself — a
    // dynamic/env-driven zod object key collapses every other field's
    // inferred type (see lib/validation.ts comment). app/api/contact/route.ts
    // reads this field off the raw JSON body before calling this schema.
    expect(getHoneypotFieldName()).toBe("company_website");
    // Zod objects silently strip unknown keys by default, so a filled
    // honeypot value here does not by itself fail schema validation.
    const result = contactFormSchema.safeParse({
      ...validPayload,
      company_website: "http://spam.example",
    });
    expect(result.success).toBe(true);
  });

  it("rejects an invalid employee range", () => {
    const result = contactFormSchema.safeParse({ ...validPayload, employeeRange: "1000+" });
    expect(result.success).toBe(false);
  });
});

describe("normalizeContactPayload", () => {
  it("turns a completely empty body into friendly per-field messages, not generic type errors", () => {
    const result = contactFormSchema.safeParse(normalizeContactPayload({}));
    expect(result.success).toBe(false);
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message);
      expect(messages).toContain("Enter your full name");
      expect(messages).toContain("Select an employee range");
      expect(messages).toContain("Select a role");
      expect(messages).toContain("Select a state");
      expect(messages).toContain("Consent is required to submit this form");
      expect(messages.some((m) => m.includes("expected string"))).toBe(false);
    }
  });

  it("passes a fully-formed payload through unchanged in effect", () => {
    const result = contactFormSchema.safeParse(normalizeContactPayload(validPayload));
    expect(result.success).toBe(true);
  });
});

describe("honeypot detection (app/api/contact/route.ts)", () => {
  it("flags a filled honeypot field as a bot submission", () => {
    expect(isHoneypotFilled({ company_website: "http://spam.example" })).toBe(true);
  });

  it("does not flag an empty or missing honeypot field", () => {
    expect(isHoneypotFilled({ company_website: "" })).toBe(false);
    expect(isHoneypotFilled({})).toBe(false);
    expect(isHoneypotFilled(null)).toBe(false);
  });
});
