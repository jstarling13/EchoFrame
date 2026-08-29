/**
 * Single source of truth for O1-O5 commercial facts, mirrored from
 * /stripe/product_catalog.json and /strategy/DECISION_LOG.md. Website copy,
 * Stripe product/price sync, and proposal generation must all read from
 * here so names/prices/deposits/milestones cannot drift out of sync (Test
 * Plan: "Business consistency").
 *
 * PAYMENT MODEL — read before touching this file.
 *
 * `totalUsd` is the full contract value. It is NEVER charged directly by
 * Stripe Checkout for O2-O4. Checkout only ever charges the single
 * milestone whose `method` is "checkout" (the deposit for O2-O4, the full
 * amount for O1, or one month for O5). All other milestones have
 * `method: "invoice"` and are billed later via a staff-issued Stripe
 * Invoice against the signed SOW — they are intentionally NOT synced as
 * public, reusable Stripe Prices (see scripts/stripe/create-products.ts
 * and STRIPE_SPECIFICATION.md "Object strategy": "Do not encode every
 * milestone as a public reusable price unless operationally useful").
 *
 * This split exists because of a real defect found in a pre-merge audit:
 * an earlier version of this file collapsed "total contract value" and
 * "amount Stripe should charge today" into one `priceUsd` field, which
 * would have made Checkout charge the FULL O2/O3/O4 contract price
 * instead of the deposit. Do not re-introduce a single combined field.
 */

export type OfferCode = "O1" | "O2" | "O3" | "O4" | "O5";

export type MilestoneMethod = "checkout" | "invoice";

export interface Milestone {
  /** Stable identifier, used in Stripe metadata for reconciliation. */
  id: string;
  label: string;
  amountUsd: number;
  /** Human-readable trigger condition, e.g. "After blueprint approval". */
  trigger: string;
  /**
   * "checkout" = the one milestone the public website can charge via
   * Stripe Checkout/a Subscription. "invoice" = billed later by staff via
   * a Stripe Invoice tied to the signed SOW; never exposed as a public
   * checkout button or public Price.
   */
  method: MilestoneMethod;
}

export interface Offer {
  code: OfferCode;
  slug: string;
  name: string;
  billing: "one_time" | "recurring";
  interval?: "month";
  /** Full contract value. Null for O5, which has no fixed total. */
  totalUsd: number | null;
  /** O5 only: the contractual minimum commitment length. */
  initialTermMonths?: number;
  /** O5 only: recurringUsd * initialTermMonths, for display only. */
  initialTermTotalUsd?: number;
  /**
   * Ordered payment milestones. Exactly one entry must have
   * method "checkout" — see getCheckoutMilestone(). The rest, if any,
   * have method "invoice".
   */
  milestones: Milestone[];
  paymentSchedule: string;
  duration: string;
  summary: string;
  deliverables: string[];
  exclusions: string[];
  /** Env var holding the Stripe Price ID for the "checkout" milestone only. */
  stripeCheckoutPriceEnvVar: string;
}

export const OFFERS: Offer[] = [
  {
    code: "O1",
    slug: "workflow-diagnostic",
    name: "Workflow Opportunity Diagnostic",
    billing: "one_time",
    totalUsd: 2500,
    milestones: [
      {
        id: "full",
        label: "Full payment",
        amountUsd: 2500,
        trigger: "Before kickoff",
        method: "checkout",
      },
    ],
    paymentSchedule: "100% prepaid before kickoff",
    duration: "10 business days",
    summary:
      "Up to 3 departments, 8 interviews, 12 workflows inventoried. Readiness score, ranked opportunity register, one current-state map, 90-day roadmap.",
    deliverables: [
      "Readiness score",
      "Ranked opportunity register",
      "One current-state map",
      "90-day roadmap",
    ],
    exclusions: [
      "Software licenses",
      "Production integrations",
      "Regulated decision automation",
    ],
    stripeCheckoutPriceEnvVar: "STRIPE_PRICE_O1",
  },
  {
    code: "O2",
    slug: "build-sprint",
    name: "Workflow Build Sprint",
    billing: "one_time",
    totalUsd: 7500,
    milestones: [
      {
        id: "deposit",
        label: "Deposit",
        amountUsd: 3750,
        trigger: "Before kickoff",
        method: "checkout",
      },
      {
        id: "final",
        label: "Final payment",
        amountUsd: 3750,
        trigger: "Before production launch",
        method: "invoice",
      },
    ],
    paymentSchedule: "50% before kickoff, 50% before production launch",
    duration: "4 weeks",
    summary:
      "One department; up to 2 medium-complexity workflows and 10 users. Workflow designs, configured solution, test evidence, SOPs, prompt library, admin handoff.",
    deliverables: [
      "Workflow designs",
      "Configured solution",
      "Test evidence",
      "SOPs",
      "Prompt library",
      "Admin handoff",
    ],
    exclusions: [
      "Custom enterprise software",
      "Migrations",
      "24/7 support",
      "Regulated autonomous decisions",
    ],
    stripeCheckoutPriceEnvVar: "STRIPE_PRICE_O2",
  },
  {
    code: "O3",
    slug: "transformation",
    name: "AI Operations Transformation",
    billing: "one_time",
    totalUsd: 18000,
    milestones: [
      {
        id: "deposit",
        label: "Deposit",
        amountUsd: 7200,
        trigger: "Before kickoff",
        method: "checkout",
      },
      {
        id: "blueprint",
        label: "Blueprint milestone",
        amountUsd: 5400,
        trigger: "After blueprint approval",
        method: "invoice",
      },
      {
        id: "launch",
        label: "Launch milestone",
        amountUsd: 5400,
        trigger: "Before launch",
        method: "invoice",
      },
    ],
    paymentSchedule:
      "40% before kickoff, 30% after approved blueprint, 30% before launch",
    duration: "8-10 weeks",
    summary:
      "Up to 3 departments, 5 workflows, 30 users. Blueprint, implementation plan, implemented workflows, governance pack, training, ROI baseline, final handoff.",
    deliverables: [
      "Blueprint",
      "Implementation plan",
      "Implemented workflows",
      "Governance pack",
      "Training",
      "ROI baseline",
      "Final handoff",
    ],
    exclusions: [
      "ERP replacement",
      "Unscoped data cleanup",
      "Custom mobile apps",
      "Legal compliance certification",
    ],
    stripeCheckoutPriceEnvVar: "STRIPE_PRICE_O3",
  },
  {
    code: "O4",
    slug: "enterprise",
    name: "Enterprise AI Operations Program",
    billing: "one_time",
    totalUsd: 45000,
    milestones: [
      {
        id: "deposit",
        label: "Deposit",
        amountUsd: 13500,
        trigger: "Kickoff",
        method: "checkout",
      },
      {
        id: "blueprint",
        label: "Blueprint milestone",
        amountUsd: 11250,
        trigger: "After blueprint approval",
        method: "invoice",
      },
      {
        id: "acceptance",
        label: "Implementation acceptance milestone",
        amountUsd: 11250,
        trigger: "After implementation acceptance",
        method: "invoice",
      },
      {
        id: "handoff",
        label: "Final handoff milestone",
        amountUsd: 9000,
        trigger: "Before final handoff",
        method: "invoice",
      },
    ],
    paymentSchedule:
      "30% kickoff, 25% blueprint approval, 25% implementation acceptance, 20% before final handoff",
    duration: "16-20 weeks",
    summary:
      "Up to 6 departments, 12 workflows, 100 users; custom scope above this level. Portfolio roadmap, governance, implementations, change management, train-the-trainer, ROI dashboard.",
    deliverables: [
      "Portfolio roadmap",
      "Governance",
      "Implementations",
      "Change management",
      "Train-the-trainer",
      "ROI dashboard",
    ],
    exclusions: [
      "Third-party license fees",
      "Extensive data engineering",
      "Formal legal/security attestations",
    ],
    stripeCheckoutPriceEnvVar: "STRIPE_PRICE_O4",
  },
  {
    code: "O5",
    slug: "support",
    name: "Workflow Assurance & Enablement",
    billing: "recurring",
    interval: "month",
    totalUsd: null,
    initialTermMonths: 3,
    initialTermTotalUsd: 7500,
    milestones: [
      {
        id: "monthly",
        label: "Monthly payment",
        amountUsd: 2500,
        trigger: "Monthly in advance",
        method: "checkout",
      },
    ],
    paymentSchedule: "Monthly in advance; 3-month initial contractual term",
    duration: "Monthly; 3-month initial term",
    summary:
      "Up to 8 support hours, 2 minor workflow changes, monitoring review. Health report, issue log, improvements, office hours, quarterly value review.",
    deliverables: [
      "Health report",
      "Issue log",
      "Improvements",
      "Office hours",
      "Quarterly value review",
    ],
    exclusions: [
      "Net-new systems",
      "24/7 monitoring",
      "Unlimited revisions",
    ],
    stripeCheckoutPriceEnvVar: "STRIPE_PRICE_O5_MONTHLY",
  },
];

export function getOffer(code: OfferCode): Offer {
  const offer = OFFERS.find((o) => o.code === code);
  if (!offer) throw new Error(`Unknown offer code: ${code}`);
  return offer;
}

/**
 * The single milestone Stripe Checkout is allowed to charge for this
 * offer. Throws if the offer's milestone data is malformed (not exactly
 * one "checkout" milestone) — this is a deliberate fail-fast guard so a
 * future data-entry mistake can never silently make Checkout charge the
 * wrong amount, including the full contract total.
 */
export function getCheckoutMilestone(offer: Offer): Milestone {
  const checkoutMilestones = offer.milestones.filter(
    (m) => m.method === "checkout"
  );
  if (checkoutMilestones.length !== 1) {
    throw new Error(
      `Offer ${offer.code} must have exactly one checkout milestone, found ${checkoutMilestones.length}`
    );
  }
  return checkoutMilestones[0]!;
}

/** Milestones billed later via a staff-issued Stripe Invoice, not public Checkout. */
export function getInvoiceMilestones(offer: Offer): Milestone[] {
  return offer.milestones.filter((m) => m.method === "invoice");
}

/** Sum of all milestone amounts — must equal totalUsd for one-time offers. */
export function sumMilestones(offer: Offer): number {
  return offer.milestones.reduce((sum, m) => sum + m.amountUsd, 0);
}

/** Amount due today at checkout — the deposit, full payment, or one month. */
export function getDueAtCheckoutUsd(offer: Offer): number {
  return getCheckoutMilestone(offer).amountUsd;
}

/** Headline price shown on cards/tables: total for one-time offers, monthly rate for O5. */
export function getDisplayPriceUsd(offer: Offer): number {
  if (offer.billing === "recurring") {
    return getDueAtCheckoutUsd(offer);
  }
  if (offer.totalUsd === null) {
    throw new Error(`One-time offer ${offer.code} is missing totalUsd`);
  }
  return offer.totalUsd;
}

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}
