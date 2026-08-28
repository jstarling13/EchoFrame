/**
 * Single source of truth for O1-O5 commercial facts, mirrored from
 * /stripe/product_catalog.json and /strategy/DECISION_LOG.md. Website copy,
 * Stripe product sync, and proposal generation must all read from here so
 * names/prices/deposits/schedules cannot drift out of sync (Test Plan:
 * "Business consistency").
 */

export type OfferCode = "O1" | "O2" | "O3" | "O4" | "O5";

export interface Offer {
  code: OfferCode;
  slug: string;
  name: string;
  priceUsd: number;
  depositUsd: number;
  billing: "one_time" | "recurring";
  interval?: "month";
  paymentSchedule: string;
  duration: string;
  summary: string;
  deliverables: string[];
  exclusions: string[];
  stripePriceEnvVar: string;
}

export const OFFERS: Offer[] = [
  {
    code: "O1",
    slug: "workflow-diagnostic",
    name: "Workflow Opportunity Diagnostic",
    priceUsd: 2500,
    depositUsd: 2500,
    billing: "one_time",
    paymentSchedule: "100% prepaid",
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
    stripePriceEnvVar: "STRIPE_PRICE_O1",
  },
  {
    code: "O2",
    slug: "build-sprint",
    name: "Workflow Build Sprint",
    priceUsd: 7500,
    depositUsd: 3750,
    billing: "one_time",
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
    stripePriceEnvVar: "STRIPE_PRICE_O2",
  },
  {
    code: "O3",
    slug: "transformation",
    name: "AI Operations Transformation",
    priceUsd: 18000,
    depositUsd: 7200,
    billing: "one_time",
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
    stripePriceEnvVar: "STRIPE_PRICE_O3",
  },
  {
    code: "O4",
    slug: "enterprise",
    name: "Enterprise AI Operations Program",
    priceUsd: 45000,
    depositUsd: 13500,
    billing: "one_time",
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
    stripePriceEnvVar: "STRIPE_PRICE_O4",
  },
  {
    code: "O5",
    slug: "support",
    name: "Workflow Assurance & Enablement",
    priceUsd: 2500,
    depositUsd: 2500,
    billing: "recurring",
    interval: "month",
    paymentSchedule: "Monthly in advance; 3-month initial term",
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
    stripePriceEnvVar: "STRIPE_PRICE_O5_MONTHLY",
  },
];

export function getOffer(code: OfferCode): Offer {
  const offer = OFFERS.find((o) => o.code === code);
  if (!offer) throw new Error(`Unknown offer code: ${code}`);
  return offer;
}

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}
