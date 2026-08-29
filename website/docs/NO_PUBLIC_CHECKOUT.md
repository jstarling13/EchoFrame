# Why there is no public Checkout button for O1-O5

**This is intentional, not an unfinished feature.**

White Oak Operations sells scoped professional services (consulting,
implementation, training, ownership transfer), not a self-serve product.
A stranger clicking "buy" on a marketing page and immediately being
charged does not fit that model — there is no scope agreement, no signed
contract, and no verified fit at that point. Nothing on this site should
let that happen, for O1 through O5.

## The approved client journey

```
Fit call → Qualification → Proposal → Signed MSA/SOW
  → Private Stripe deposit invoice or payment link → Kickoff
```

Every offer page (`/workflow-diagnostic`, `/build-sprint`,
`/transformation`, `/enterprise`, `/support`) and `/services` render this
explicitly via `components/EngagementJourney.tsx`, immediately next to
pricing. The only call-to-action on every offer page is **"Book a fit
call,"** linking to `/contact` — never a payment action.

## What exists in code vs. what's exposed publicly

`app/api/stripe/checkout/route.ts` exists and is fully implemented and
tested (see `PROMOTION_AUDIT_REPORT.md` for the payment-architecture
audit). It is reachable only as a server API endpoint — **no page, link,
or button anywhere in the UI calls it.** Its purpose is to let staff
generate a private Checkout Session/payment-link URL to send a qualified
client directly (by email, after a signed SOW), not to be a public
storefront action. This split is deliberate:

- The route enforces the correct amount server-side (never a
  client-supplied amount — see the payment-architecture audit) and stays
  useful as the mechanism *behind* a privately-sent payment link.
- Nothing renders it as a clickable public element, so a site visitor can
  never self-serve a charge.

If a public "pay now" button is ever wanted for a specific offer in the
future, that is a deliberate product decision requiring explicit sign-off
— it does not happen by default, and nothing in the current codebase
assumes it will happen.

## Verifying this stays true

- `grep -rn "api/stripe/checkout" app components` (from `website/`)
  returns no results — confirmed as part of this documentation change.
- Every offer page's only interactive CTA is `Book a fit call` → `/contact`.
- `components/OfferDetail.tsx` and `components/OfferTable.tsx` describe
  pricing using "initial payment" language and explicitly state it is
  "invoiced privately after a signed SOW — not a public checkout."
