# Selector Interaction & Accessibility Specification

## Semantics
Use real buttons for selectable chips.

## Keyboard
- Tab reaches each option
- Enter/Space selects
- visible focus
- selection announced

## State
Use `aria-pressed` for toggle-style button state or an appropriate radio-group semantic if only one selection is allowed per question.

## Screen Readers
After step 1, announce that question 2 is now available.

After step 2, avoid disorienting focus jumps. Prefer an `aria-live` region for the result summary when appropriate.

## Contrast
Selection cannot rely only on subtle background color.
Use border, weight, icon/check if appropriate, and strong contrast.

## Motion
Small transition only. Respect reduced-motion preferences.

## Mobile
- minimum comfortable tap target
- wrapped button layout
- no tiny pill text
- no horizontal overflow

## Performance
No heavy library needed. This can be a small client component.

## Analytics
If analytics exists, events:
- `industry_selector_industry_selected`
- `industry_selector_problem_selected`
- `industry_selector_cta_clicked`

Properties:
- industry slug
- problem slug

Do not attach identifying data.

## Contact Prefill
If CTA carries context:
Prefill:
Industry: [selection]
Workflow area: [selection]

Do not auto-submit.
