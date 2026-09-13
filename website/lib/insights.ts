export interface InsightArticle {
  slug: string;
  title: string;
  description: string;
  date: string;
  readingTimeMinutes: number;
}

export const INSIGHTS_ARTICLES: InsightArticle[] = [
  {
    slug: "why-automation-projects-fail-before-the-model",
    title: "Why Most Automation Projects Fail Before the First Model Is Chosen",
    description:
      "The easiest part of an automation project is picking a tool — and picking it too early is what usually breaks the project.",
    date: "2026-09-13",
    readingTimeMinutes: 6,
  },
  {
    slug: "real-cost-of-a-manual-financial-workflow",
    title: "The Real Cost of a Manual Financial Workflow",
    description:
      "The wage attached to a task is not its full cost. A useful business case counts touch time, rework, delay, concentration risk, and management attention.",
    date: "2026-09-13",
    readingTimeMinutes: 6,
  },
  {
    slug: "working-automation-vs-reliable-operating-system",
    title: "A Working Automation Is Not Yet a Reliable Operating System",
    description:
      "A prototype proves a path can work. An operating system has to prove what happens when it doesn't.",
    date: "2026-09-13",
    readingTimeMinutes: 6,
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
