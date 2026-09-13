import {
  INDUSTRY_OPTIONS,
  INDUSTRY_CONTENT,
  PROBLEM_CONTENT,
} from "@/lib/industrySelector";
import {
  TRAVEL_FEE_SUMMARY,
  PRICING_LINE_ITEMS,
  SERVICE_CAPABILITIES,
} from "@/lib/services";
import type { MatcherDocument } from "@/lib/problemMatcher";

/**
 * Explicit allowlist, not a generic walk of the two content modules —
 * `slug` and `category` fields are internal identifiers (e.g.
 * "bookkeeping-automation") that would otherwise be indexed as
 * standalone candidate strings and could render as raw hyphenated text
 * if they ever out-scored the real sentence describing the same thing.
 * Every string below is copied verbatim from the two source modules;
 * only the joining words ("Common workflows:", ":", etc.) are new, and
 * they introduce no new claim, price, or capability.
 */
function buildDocuments(): MatcherDocument[] {
  const documents: MatcherDocument[] = [];

  for (const option of INDUSTRY_OPTIONS) {
    const content = INDUSTRY_CONTENT[option.slug];
    if (!content) continue;
    documents.push({
      id: `industry-${option.slug}`,
      source: "industry-selector",
      path: `INDUSTRY_CONTENT.${option.slug}`,
      text: `${option.label}: ${content.message} Common workflows: ${content.workflows.join(", ")}.`,
    });
  }

  for (const [slug, content] of Object.entries(PROBLEM_CONTENT)) {
    documents.push({
      id: `problem-${slug}`,
      source: "industry-selector",
      path: `PROBLEM_CONTENT.${slug}`,
      text: `${content.headline} Typical capabilities: ${content.capabilities.join(", ")}. ${content.firstQuestion}`,
    });
  }

  documents.push({
    id: "services-travel-fee",
    source: "services",
    path: "TRAVEL_FEE_SUMMARY",
    text: `Travel fee: ${TRAVEL_FEE_SUMMARY}`,
  });

  PRICING_LINE_ITEMS.forEach((item, index) => {
    documents.push({
      id: `services-pricing-${index}`,
      source: "services",
      path: `PRICING_LINE_ITEMS[${index}]`,
      text: `${item.label}: ${item.detail}`,
    });
  });

  for (const service of SERVICE_CAPABILITIES) {
    documents.push({
      id: `services-capability-${service.slug}`,
      source: "services",
      path: `SERVICE_CAPABILITIES.${service.slug}`,
      text: `${service.name}: ${service.blurb}`,
    });
  }

  // SIZE_NOTE is a private module constant (not exported from
  // lib/industrySelector.ts), so team-size context isn't indexed here —
  // only industry, problem, and service/pricing content.

  return documents;
}

export const PROBLEM_MATCHER_DOCUMENTS: MatcherDocument[] = buildDocuments();
