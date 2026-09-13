# Integration notes

## Recommended placement

Put the matcher on `/contact`, below the page's concise introduction and above the fit-call form. It helps a visitor frame the problem immediately before the existing conversion step, without turning the homepage into another interactive-product demo.

If `/contact` is already dense, use a new `/problem-matcher` page and add one restrained teaser link from `/services` or the lower portion of `/contact`. Do not add the full widget to the homepage. A homepage teaser is optional, not required.

## Ready-to-drop files

Copy these paths into the same paths in the Next.js project:

- `components/ProblemMatcher.tsx`
- `lib/problemMatcher.ts`
- `lib/problemMatcherCatalog.ts`

Then import and render the component in the chosen server page:

```tsx
import ProblemMatcher from "@/components/ProblemMatcher";

// Inside the page JSX at the chosen location:
<ProblemMatcher />;
```

The catalog uses namespace imports from `lib/industrySelector.ts` and `lib/services.ts`, so it does not assume undocumented export names or content shapes. It recursively indexes existing exported strings of at least 18 characters. Inspect the rendered matches to ensure neither module exports internal strings that should not appear as visitor-facing copy.

## Styling

The component intentionally contains semantic class names but no invented design system. Map these classes to the site's existing spacing, type, form, button, focus, border, and result-card rules:

- `.problem-matcher`
- `.problem-matcher__intro`
- `.problem-matcher__form`
- `.problem-matcher__meta`
- `.problem-matcher__results`

Keep visible keyboard focus, sufficient color contrast, a persistent label, and an obvious error/fallback state. The results region uses `aria-live`; avoid adding animations that repeatedly reannounce it.

## Approval items before merge

1. Replace the textarea's explicitly marked placeholder with reviewed example copy, or remove the placeholder.
2. Review what `problemMatcherCatalog.ts` extracts from the real modules. If needed, replace namespace extraction with an explicit allowlist of approved exports.
3. Tune `minimumScore` against a small test set of real or synthetic descriptions. Favor false fallbacks over false claims.
4. Confirm the fallback's reference to the fit-call request matches the actual contact page wording and link flow.
5. Add project-native CSS. No stylesheet is included because the current tokens and established classes were not supplied.
6. Run the project's formatter, typecheck, tests, and production build.

## Suggested acceptance tests

- A description using exact terms from each known industry/problem/service returns that approved passage.
- A description with fewer than two meaningful words returns the fallback.
- Gibberish returns the fallback.
- No result contains text absent from the two indexed modules.
- Duplicate source strings appear once.
- The textarea stops at 800 characters.
- Submit and results work by keyboard and with a screen reader.
- No network request occurs when the matcher is used.

## Privacy behavior of this sample

The matcher runs locally in the visitor's browser and does not submit, retain, or transmit the typed description. Confirm that analytics or session-replay tooling on the live site is configured not to capture textarea contents. If the description is later copied into or attached to the contact form, the existing form disclosure and policy must cover that separate submission.
