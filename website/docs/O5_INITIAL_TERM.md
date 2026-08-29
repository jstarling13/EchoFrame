# O5 — how the 3-month initial term is actually enforced

**Status: contractual only. Stripe enforces none of this technically.**
Final wording below is a working draft and is **pending attorney review**
(see `legal/ATTORNEY_REVIEW_REQUIRED.md`) — do not publish it as final
contract or website language without counsel sign-off.

## What Stripe does and does not do

Stripe Subscriptions bill `$2,500` monthly in advance for O5. That is the
entire extent of what Stripe enforces. Stripe does **not**:

- Prevent a subscription from being canceled before 3 months have elapsed
  (via the Stripe Dashboard, the API, or any future customer portal).
- Know or care about "initial terms," minimum commitments, or early-
  termination fees. Those concepts don't exist in Stripe's data model.
- Automatically bill a client for the remaining balance of an initial term
  if they cancel early.

So if the only enforcement mechanism were "whatever Stripe does by
default," a client could cancel after one month and owe nothing further
through Stripe. **That would misrepresent the commercial deal** (three
one-month payments = $7,500 minimum, per `strategy/DECISION_LOG.md`).

## What actually enforces the 3-month term

**The signed Statement of Work / Master Services Agreement is the sole
enforcement mechanism.** The contract is the commercial authority, not
Stripe. Practically:

1. The client signs an SOW referencing O5 and its 3-month initial term
   before the first Stripe subscription payment is collected.
2. If a client cancels the Stripe subscription (or requests cancellation)
   before 3 months have elapsed, `app/api/stripe/webhook/route.ts` detects
   this (via `lib/subscription-term.ts`) and logs a flagged event —
   `stripe_subscription_cancelled_within_initial_term` — for a human to
   follow up on.
3. That follow-up is **manual and contract-based**: the owner (or
   whoever handles billing) refers to the signed SOW's early-termination
   clause and invoices the client directly for the remaining committed
   amount, if the contract says to. Nothing in this codebase auto-charges
   that amount, and nothing blocks the Stripe cancellation from going
   through — see "Do not create a punitive or legally unreviewed
   cancellation mechanism" in the audit that produced this document.

## What the website must not imply

The website and any cancellation-facing copy must not say or imply that a
client can cancel the Stripe subscription and walk away from the
remaining initial-term commitment with no further obligation. Current
copy (`app/support/page.tsx`, `components/OfferDetail.tsx`) states the
3-month term and links here. It does not currently state a specific
early-termination fee or process, because that wording has not been
drafted or reviewed by counsel yet — see "Open items for counsel" below.

## Open items for counsel

- Whether cancellation before the initial term ends should: (a) require
  paying the full remaining committed amount, (b) require a smaller
  cancellation fee, or (c) be handled case-by-case.
- Whether that obligation should be disclosed on the public website at
  all, or only in the signed SOW/MSA.
- Whether "3-month initial term" should auto-renew, convert to
  month-to-month, or require an explicit renewal after month 3.
- Exact cancellation notice period and method (e.g. written notice via a
  specific channel).

Until these are resolved, `STRIPE_SPECIFICATION.md`'s existing baseline
stands: *"O5 cancel at period end after initial term unless contract says
otherwise."*
