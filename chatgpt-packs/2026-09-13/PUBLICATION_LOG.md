# Publication Log — 12_EchoFrame_Authority_Proof_System

Records what Jacob explicitly approved for publication from this pack, and
under what corrections. Not a legal document — a record of the approval
conversation, kept alongside the source pack for future reference.

## Approved and published (2026-09-13)

- **Case-study figures:** 13-location, 48-to-6-hours/week, June–September
  2026 observation period confirmed accurate. Homepage headline, title,
  and proof section rewritten to match. Old claims ("five hours a day,"
  "15 locations," "fully automated") removed site-wide — verified by
  full-repo grep before commit.
- **Case study page** published at
  `/insights/from-three-16-hour-days-to-six-hours-a-week`, using the
  approved public formulation verbatim in its closing proof block.
- **Fifth Insights article** published at
  `/insights/what-an-87-5-percent-reduction-actually-required` (retitled
  from the pack's "...Weekly Accounting Labor..." to "...Weekly
  Processing Time..." per Jacob's instruction that the reduction is
  specifically in processing time, not labor cost, headcount, or errors).
- **About page** expanded with the confirmed Comcast (Emory academic
  exercise, not client work) and Blue Eagle Capital (Emory
  student-managed fund, not an employer) context, using Jacob's exact
  approved wording — "presented recommendations to the investment
  committee for review," not "secured approvals."

## Withheld per Jacob's explicit instructions — do not add without new approval

- Exact "13 locations" figure — replaced with "multiple locations" /
  "multi-location" everywhere public, per Jacob's identifiability concern.
- SRG Business Services LLC, Dunkin&rsquo;, Baskin-Robbins, any revenue
  figure, and the client's relationship to Jacob (his aunt) — never
  published; the case study and fifth article both describe the client
  only as an anonymized multi-location food-service accounting operation.
- The $650 implementation fee.
- The ~2.5-day initial build time.
- The informal ~80% initial-accuracy estimate (current accuracy was
  never formally measured, so no accuracy figure is published at all).
- A public testimonial — none exists and none will be requested for
  public use. `TESTIMONIAL_AND_REFERENCE_PLAYBOOK.md` stays an internal
  operating document only.
- The "private reference available after qualification" line — Jacob
  declined to add this to the public site at this time.

## Verification performed before publishing

- Full-repo grep for "five hours," "15 locations," "15-location," "fully
  automated," "13 locations," "aunt"/"family member," "SRG," "Dunkin,"
  "Baskin," "$650," "2.5-day," and the 80%-accuracy estimate — all clear.
- `npx tsc --noEmit`, `npm test` (76/76 passing), and `npm run build`
  (production build, all routes statically generated) — all clean.
- Responsive check at 375px (mobile) and 1280px (desktop): no
  page-level horizontal overflow; the case-study table scrolls within
  its own container as designed.
