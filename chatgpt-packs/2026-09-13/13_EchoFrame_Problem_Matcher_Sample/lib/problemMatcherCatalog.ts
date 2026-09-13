import * as industrySelectorContent from "@/lib/industrySelector";
import * as servicesContent from "@/lib/services";
import {
  documentsFromExport,
  type MatcherDocument,
} from "@/lib/problemMatcher";

/**
 * This indexes strings already exported by EchoFrame's approved content modules.
 * No response copy or capability is introduced here.
 */
export const PROBLEM_MATCHER_DOCUMENTS: MatcherDocument[] = [
  ...documentsFromExport(industrySelectorContent, "industry-selector"),
  ...documentsFromExport(servicesContent, "services"),
];
