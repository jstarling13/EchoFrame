import { describe, expect, it } from "vitest";
import {
  resolveSubmissionOutcome,
  shouldReturnServiceUnavailable,
} from "../lib/lead-routing";

describe("resolveSubmissionOutcome", () => {
  it("spam: honeypot filled short-circuits regardless of destination config", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: true,
        crmConfigured: true,
        emailConfigured: true,
        crmDelivered: false,
        emailSent: false,
      })
    ).toBe("spam");
  });

  it("email-only: succeeds when the one configured destination succeeds", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: false,
        emailConfigured: true,
        crmDelivered: false,
        emailSent: true,
      })
    ).toBe("delivered");
  });

  it("email-only: fails when the one configured destination fails", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: false,
        emailConfigured: true,
        crmDelivered: false,
        emailSent: false,
      })
    ).toBe("failed");
  });

  it("CRM-only: succeeds when the one configured destination succeeds", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: false,
        crmDelivered: true,
        emailSent: false,
      })
    ).toBe("delivered");
  });

  it("CRM-only: fails when the one configured destination fails", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: false,
        crmDelivered: false,
        emailSent: false,
      })
    ).toBe("failed");
  });

  it("both configured, both succeed: delivered", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: true,
        crmDelivered: true,
        emailSent: true,
      })
    ).toBe("delivered");
  });

  it("both configured, one fails: partial", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: true,
        crmDelivered: true,
        emailSent: false,
      })
    ).toBe("partial");

    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: true,
        crmDelivered: false,
        emailSent: true,
      })
    ).toBe("partial");
  });

  it("both configured, both fail: failed (total failure)", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: true,
        emailConfigured: true,
        crmDelivered: false,
        emailSent: false,
      })
    ).toBe("failed");
  });

  it("neither configured: failed (local-development no-op case, gated at the route level)", () => {
    expect(
      resolveSubmissionOutcome({
        isHoneypotFilled: false,
        crmConfigured: false,
        emailConfigured: false,
        crmDelivered: false,
        emailSent: false,
      })
    ).toBe("failed");
  });
});

describe("shouldReturnServiceUnavailable", () => {
  it("returns 503-worthy for failed outcomes in production", () => {
    expect(shouldReturnServiceUnavailable("failed", true)).toBe(true);
  });

  it("does NOT return 503-worthy for failed outcomes outside production (local no-op behavior)", () => {
    expect(shouldReturnServiceUnavailable("failed", false)).toBe(false);
  });

  it("never returns 503-worthy for delivered, partial, or spam, in any environment", () => {
    for (const outcome of ["delivered", "partial", "spam"] as const) {
      expect(shouldReturnServiceUnavailable(outcome, true)).toBe(false);
      expect(shouldReturnServiceUnavailable(outcome, false)).toBe(false);
    }
  });
});
