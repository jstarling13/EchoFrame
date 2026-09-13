export interface InsightArticle {
  slug: string;
  title: string;
  description: string;
  date: string;
  readingTimeMinutes: number;
  kind?: "Case Study";
}

/**
 * Deliberately short. Jacob's call: six articles all dated the same day
 * with near-identical reading times read as a same-day content dump, not
 * an ongoing publishing practice — a real credibility problem, not a
 * cosmetic one. Rather than backdate the rest to fake an earlier history
 * (dishonest), the other four (why-automation-projects-fail-before-the-
 * model, real-cost-of-a-manual-financial-workflow,
 * working-automation-vs-reliable-operating-system,
 * what-an-87-5-percent-reduction-actually-required) stay written and in
 * place under app/insights/ but out of this list, to be added back one
 * at a time with real publish dates as they actually go live. Add
 * `robots: {index:false}` was applied to those pages so they don't get
 * indexed while unlisted.
 */
export const INSIGHTS_ARTICLES: InsightArticle[] = [
  {
    slug: "from-three-16-hour-days-to-six-hours-a-week",
    title: "From Three 16-Hour Processing Days to Six Hours a Week",
    description:
      "An anonymized case study: a client-tracked 87.5% reduction in weekly processing time for a multi-location food-service accounting operation — including what the result does and does not prove.",
    date: "2026-09-13",
    readingTimeMinutes: 9,
    kind: "Case Study",
  },
  {
    slug: "evaluating-an-ai-automation-proposal",
    title: "How to Evaluate an AI Automation Proposal Before You Buy It",
    description:
      "A buyer's checklist: the questions to ask about scope, baselines, human review, data flow, failure handling, ownership, and measurement before approving the work.",
    date: "2026-09-13",
    readingTimeMinutes: 7,
  },
];
