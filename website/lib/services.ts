/**
 * EchoFrame's current commercial model: hourly, quoted per client — not the
 * fixed O1-O5 packages in lib/offers.ts (kept in place, unused, so nothing
 * that already reads from it breaks). Every engagement is billed the same
 * simple way: hourly rate, a travel fee for onsite trips, and a daily food
 * stipend for onsite work. There is no self-serve checkout for any of
 * this — see components/EngagementJourney.tsx for the actual client path.
 */

export const HOURLY_RATE_USD = 40;

export const FOOD_STIPEND_USD_PER_DAY = 50;

export const TRAVEL_FEE_SUMMARY =
  "A flat travel fee to cover the trip — mileage or airfare and lodging — quoted upfront based on distance. A typical single-day regional trip runs around $1,250; it's confirmed before anything is booked.";

export interface PricingLineItem {
  label: string;
  detail: string;
}

export const PRICING_LINE_ITEMS: PricingLineItem[] = [
  {
    label: "First conversation",
    detail:
      "Free — a focused 20-30 minute call to confirm the workflow is real and worth solving. No mapping, no design work, no bill.",
  },
  {
    label: "Professional time",
    detail: `$${HOURLY_RATE_USD}/hour, billed for actual hours worked — including paid discovery when a workflow is too complex to scope on the free call`,
  },
  {
    label: "Travel fee",
    detail: TRAVEL_FEE_SUMMARY,
  },
  {
    label: "Onsite food stipend",
    detail: `$${FOOD_STIPEND_USD_PER_DAY}/day for any day worked onsite at a client location`,
  },
];

export interface ServiceCapability {
  slug: string;
  name: string;
  category: string;
  blurb: string;
}

/**
 * Broad capability areas, not priced SKUs. Deliberately not a long list of
 * separately-priced "products" — one hourly rate covers all of it, scoped
 * and quoted after a short conversation about the actual problem.
 */
export const SERVICE_CAPABILITIES: ServiceCapability[] = [
  {
    slug: "workflow-discovery",
    name: "EchoFrame Pulse™ — Workflow Discovery & Opportunity Mapping",
    category: "Get started",
    blurb:
      "A focused first visit to take the operation's pulse: see how work actually moves through the business today and build a plain-language list of what's worth fixing first.",
  },
  {
    slug: "bookkeeping-automation",
    name: "Bookkeeping & Financial Workflow Automation",
    category: "Financial operations",
    blurb:
      "Deposit matching, bank and card reconciliation, bill intake and approval routing, payroll entry prep — built to sit cleanly inside QuickBooks or whatever the books already run on.",
  },
  {
    slug: "multi-entity-tracking",
    name: "Multi-Entity & Intercompany Tracking",
    category: "Financial operations",
    blurb:
      "For owners running more than one business or tax ID: a master view across entities without blending the books.",
  },
  {
    slug: "process-automation",
    name: "Process & Workflow Automation",
    category: "Operations",
    blurb:
      "Repetitive, manual work in spreadsheets, inboxes, or between disconnected tools, rebuilt as a dependable automated workflow.",
  },
  {
    slug: "customer-communication",
    name: "Customer Communication & Lead Follow-Up",
    category: "Operations",
    blurb:
      "AI-assisted intake, scheduling, and follow-up so leads and customer messages stop sitting unanswered.",
  },
  {
    slug: "reporting-dashboards",
    name: "Reporting & Owner Dashboards",
    category: "Operations",
    blurb:
      "One clean, current view of how the business is doing, built from the systems already in place — no new software to buy.",
  },
  {
    slug: "staff-training",
    name: "Staff Training",
    category: "Team enablement",
    blurb:
      "Hands-on training so the team can run and extend what's built, not just click the button someone else wired up.",
  },
  {
    slug: "systems-security-review",
    name: "Systems & Security Review",
    category: "Team enablement",
    blurb:
      "A clear-eyed look at who can access what, so as the business grows, its data grows more secure right alongside it.",
  },
  {
    slug: "ongoing-consulting",
    name: "EchoFrame Continuum™ — Ongoing AI Consulting",
    category: "Stay current",
    blurb:
      "Month to month, by the hour: troubleshooting, new automations as they come up, and staying current on whatever the newest useful AI tools can do for the business.",
  },
];

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}
