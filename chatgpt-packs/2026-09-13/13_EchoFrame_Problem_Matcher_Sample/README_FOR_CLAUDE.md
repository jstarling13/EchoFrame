# Instructions for Claude Code

## Goal

Integrate a deterministic free-text problem matcher into EchoFrame without adding an AI provider, API route, database, or new claims. The site’s existing content remains the only source of visitor-facing service information.

Read `DESIGN_AND_TRADEOFFS.md` and `INTEGRATION_NOTES.md` before editing the project.

## Ready to drop in

These files are implementation-ready and may be copied to the corresponding project paths:

- `components/ProblemMatcher.tsx`
- `lib/problemMatcher.ts`
- `lib/problemMatcherCatalog.ts`

After copying, inspect the actual exports from `lib/industrySelector.ts` and `lib/services.ts`. The catalog intentionally uses namespace imports and recursively extracts existing strings because this handoff was not given the exact TypeScript shapes. If those modules export internal/non-display strings, replace recursive extraction with an explicit allowlist. Do not alter or invent source copy.

## Integration work allowed without a new product decision

- Render `<ProblemMatcher />` on `/contact` in the location described in `INTEGRATION_NOTES.md`.
- Apply existing site classes/tokens so the component visually matches `IndustrySelector.tsx`.
- Adjust imports to match the repository's existing alias convention.
- Add unit tests and accessibility tests using dependencies already present.
- Fix TypeScript or lint issues without changing product behavior.

## Requires Jacob's explicit approval first

- Adding the full matcher to the homepage.
- Creating a new `/problem-matcher` page instead of using `/contact`.
- Adding or changing visitor-facing example copy, service language, pricing, claims, synonyms, thresholds that materially change matches, or analytics.
- Persisting or transmitting the description anywhere.
- Adding a database, API route, dependency, third-party service, session replay, or tracking event.
- Implementing any LLM-backed component or route.
- Adding OpenAI, Anthropic, or any other model key/package.
- Changing the Privacy Policy or Terms.

## LLM path

There is intentionally no LLM code in this package. `DESIGN_AND_TRADEOFFS.md` specifies the prerequisites, prohibitions, rate-limit expectations, cost planning range, and draft privacy wording. Do not implement that path until Jacob approves the provider, model, exact allowlist, data handling, vendor terms, budget, and counsel-reviewed policy changes.

## Completion checks

Before reporting completion:

1. Confirm the rendered result text comes only from the two existing content modules.
2. Confirm using the matcher creates no network request.
3. Run the repository's formatter, linter, typecheck, tests, and production build.
4. Test keyboard operation, focus visibility, textarea labeling, live results, empty/short input, gibberish, and the 800-character limit.
5. Report any source strings excluded from the index and every project file changed.
