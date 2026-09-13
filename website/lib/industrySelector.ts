export interface Option {
  slug: string;
  label: string;
}

export const INDUSTRY_OPTIONS: Option[] = [
  { slug: "accounting", label: "Accounting & Bookkeeping" },
  { slug: "professional-services", label: "Professional Services" },
  { slug: "real-estate", label: "Real Estate & Property" },
  { slug: "construction", label: "Construction & Trades" },
  { slug: "retail", label: "Retail & Multi-Location" },
  { slug: "recruiting", label: "Recruiting & Staffing" },
  { slug: "multi-entity", label: "Multi-Entity Businesses" },
  { slug: "other", label: "Other" },
];

export const PROBLEM_OPTIONS: Option[] = [
  { slug: "financial-workflows", label: "Financial Workflows" },
  { slug: "repetitive-admin", label: "Repetitive Admin" },
  { slug: "customer-follow-up", label: "Customer Follow-Up" },
  { slug: "reporting", label: "Reporting & Visibility" },
  { slug: "multi-entity-complexity", label: "Multi-Entity Complexity" },
  { slug: "document-intake", label: "Document Intake" },
  { slug: "staff-ai-use", label: "Staff AI Use" },
  { slug: "not-sure", label: "I'm Not Sure Yet" },
];

export const SIZE_OPTIONS: Option[] = [
  { slug: "solo", label: "Just me / a handful of people" },
  { slug: "small-team", label: "A small team (roughly 2-25)" },
  { slug: "growing", label: "Growing (roughly 25-50)" },
  { slug: "established", label: "Established (50+)" },
];

const SIZE_NOTE: Record<string, string> = {
  solo:
    "At this size, the fastest win is usually removing one manual task entirely rather than building a system around a team that doesn't exist yet.",
  "small-team":
    "At this size, the goal is usually giving one or two people back real hours a week without adding a tool nobody else learns to use.",
  growing:
    "At this size, workflows usually start breaking in the handoffs between people — that's typically where the highest-value fix is.",
  established:
    "At this size, the constraint is usually consistency across people and locations more than the workflow itself.",
};

interface IndustryContent {
  workflows: string[];
  message: string;
}

export const INDUSTRY_CONTENT: Record<string, IndustryContent> = {
  accounting: {
    workflows: [
      "deposit matching and exception queues",
      "reconciliation support",
      "client document collection",
      "bill intake/routing",
      "month-end coordination",
      "reporting",
    ],
    message:
      "Automation around professional judgment, not replacement of the professional.",
  },
  "professional-services": {
    workflows: [
      "intake",
      "document organization",
      "recurring reporting",
      "scheduling/coordination",
      "internal knowledge search",
      "follow-up",
    ],
    message:
      "For regulated professions, EchoFrame focuses on administrative workflow, not licensed professional judgment.",
  },
  "real-estate": {
    workflows: [
      "tenant/admin intake",
      "remittance/payment workflow",
      "recurring communications",
      "document routing",
      "owner reporting",
      "multi-property visibility",
    ],
    message: "Common workflows EchoFrame can evaluate in property operations.",
  },
  construction: {
    workflows: [
      "estimate intake",
      "job paperwork",
      "invoice/document routing",
      "lead follow-up",
      "status reporting",
      "recurring administrative handoffs",
    ],
    message: "Where EchoFrame can help on the admin side of the job.",
  },
  retail: {
    workflows: [
      "location reporting",
      "deposit/reconciliation support",
      "recurring admin",
      "exception reporting",
      "owner dashboards",
      "consistent process across locations",
    ],
    message: "Common workflows EchoFrame can evaluate across locations.",
  },
  recruiting: {
    workflows: [
      "intake",
      "scheduling",
      "communications",
      "status reporting",
      "administrative coordination",
    ],
    message:
      "EchoFrame does not market autonomous employment decisions or consequential candidate screening.",
  },
  "multi-entity": {
    workflows: [
      "entity-level reporting",
      "intercompany tracking support",
      "document separation",
      "owner-level visibility",
      "reconciliation/admin coordination",
    ],
    message:
      "Entity and accounting separation is preserved; professional review stays in place.",
  },
  other: {
    workflows: [
      "workflow discovery and opportunity mapping",
      "process documentation",
      "automation feasibility review",
    ],
    message:
      "If the business has a recurring workflow that is repetitive, measurable, and stable enough to map, EchoFrame can evaluate whether automation is worth doing.",
  },
};

interface ProblemContent {
  headline: string;
  capabilities: string[];
  firstQuestion: string;
}

export const PROBLEM_CONTENT: Record<string, ProblemContent> = {
  "financial-workflows": {
    headline: "Start with the repetitive work around the judgment.",
    capabilities: [
      "financial workflow automation",
      "multi-entity tracking",
      "reporting",
    ],
    firstQuestion:
      "Where is the same information being matched, checked, or re-entered by hand?",
  },
  "repetitive-admin": {
    headline: "Start with the steps nobody wants to keep doing by hand.",
    capabilities: ["process automation", "document intake", "approval/routing", "recurring reports"],
    firstQuestion: "Which task gets redone the same way, every single day?",
  },
  "customer-follow-up": {
    headline: "Start with the response that's arriving too late.",
    capabilities: ["lead intake", "scheduling", "follow-up", "pipeline visibility"],
    firstQuestion: "Where do leads or requests sit before anyone responds?",
  },
  reporting: {
    headline: "Start with the report someone assembles by hand every week.",
    capabilities: ["dashboards", "KPI reporting", "backlog/exception reporting"],
    firstQuestion: "What number do you wish you could see without asking someone to build it?",
  },
  "multi-entity-complexity": {
    headline: "Start with the view you don't have across entities.",
    capabilities: ["entity control view", "intercompany tracking support", "reporting", "document separation"],
    firstQuestion: "What can't you see across entities today without manually pulling it together?",
  },
  "document-intake": {
    headline: "Start with the documents that arrive faster than they get processed.",
    capabilities: ["extraction", "validation", "routing", "exception queue"],
    firstQuestion: "What comes in by email or upload that someone has to manually read and route?",
  },
  "staff-ai-use": {
    headline: "Start with how the team is already using AI, informally.",
    capabilities: ["training", "approved-tool review", "access/data review", "workflow-specific usage guidance"],
    firstQuestion: "What is the team already doing with AI tools that nobody has reviewed yet?",
  },
  "not-sure": {
    headline: "Start with a focused first visit to see what's actually there.",
    capabilities: ["workflow discovery and opportunity mapping"],
    firstQuestion: "What's the one process that everyone already agrees is too manual?",
  },
};

export interface SelectorResult {
  headline: string;
  startingPoints: string[];
  capabilities: string[];
  firstQuestion: string;
  industryMessage: string;
  sizeNote?: string;
}

export function getSelectorResult(
  industrySlug: string,
  problemSlug: string,
  sizeSlug?: string | null
): SelectorResult | null {
  const industry = INDUSTRY_CONTENT[industrySlug];
  const problem = PROBLEM_CONTENT[problemSlug];
  if (!industry || !problem) return null;
  return {
    headline: problem.headline,
    startingPoints: industry.workflows.slice(0, 3),
    capabilities: problem.capabilities,
    firstQuestion: problem.firstQuestion,
    industryMessage: industry.message,
    sizeNote: sizeSlug ? SIZE_NOTE[sizeSlug] : undefined,
  };
}

export function getOptionLabel(options: Option[], slug: string): string | undefined {
  return options.find((o) => o.slug === slug)?.label;
}
