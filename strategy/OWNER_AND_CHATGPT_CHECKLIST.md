# Owner & ChatGPT Checklist

**Purpose:** One consolidated list of everything still needed before Production —
split by who can actually provide it. ChatGPT can draft documents, but it
cannot invent real business facts, and drafted legal documents are not
final until a licensed attorney reviews them.

**Version:** 1.0 | **Date:** 2026-08-30

---

## A. Facts only you can provide

ChatGPT cannot invent these — they're real facts about your business.
Once you have them, hand them to ChatGPT (or me) to drop into documents
and site copy.

1. **Legal entity** — name confirmed as White Oak Operations. Still
   open: formation state, entity type (LLC/Corp/sole proprietor), DBA/
   assumed name if any, registered agent.
2. **Principal business address — provided 2026-08-30:** 17 Ridgeway
   Drive, Cataula, GA 31804. Live on About, Terms, Privacy, and the
   footer. Note: this reads as a residential address; flagged to owner,
   owner's choice to use it or switch to a virtual mailbox/registered-
   agent address later.
3. **Business phone number — provided 2026-08-30:** (706) 366-1096.
   Live on About, Terms, and the footer.
4. **Support and privacy email — provided 2026-08-30:**
   jacobstarling4313@gmail.com, used for both. Live on About, Privacy,
   and the footer. A domain-branded address (`support@`/`privacy@`) can
   replace it once a domain is live.
5. **Tax ID / EIN** status.
6. **Business bank account** — set up and ready to receive Stripe
   payouts.
7. **Insurance** — E&O / general liability policy status, if any.
8. **New York travel base and included-mile radius** — where you travel
   from, and how many miles/what area is included before travel becomes
   separately billable.
9. **Pricing display preference** — exact dollar amounts shown publicly
   (current default) vs. "starting at" language.
10. **Payment method preference** — ACH and card both accepted for
    invoices, or ACH-first.
11. **Vendor choices** — bookkeeping/accounting software, CRM (optional
    for now), scheduling tool (e.g. Calendly), analytics tool (if any),
    e-signature tool (DocuSign/HelloSign/PandaDoc/etc.). Resend is
    already the default email choice.
12. **Domain** — final domain name decision and purchase/confirmation
    (this is what eventually gets connected via IONOS).
13. **Name clearance results** — once trademark/entity-name/domain/
    common-law searches are actually run (`handoff/04_NAME_LEGAL/NAME_CLEARANCE_WORKBOOK.csv`
    has the exact search list), the real findings.
14. **Founder bio/credentials for the About page** — I left this as an
    explicit placeholder rather than inventing your background; tell me
    what you actually want said there.

## B. Documents ChatGPT can draft now — attorney review still required before going live

Once you have the facts from Section A, give them to ChatGPT and ask it
to draft:

1. Terms of Service
2. Privacy Policy
3. Master Service Agreement (MSA) template
4. Statement of Work (SOW) template, one per offer (O1–O5)
5. Mutual NDA template
6. Data Processing Agreement (DPA) — needed if any client data is
   handled
7. Cancellation/refund policy language
8. Travel/expense policy language

These stay labeled as attorney-review drafts on the site (the yellow
banner) until a real attorney signs off — that's not optional, it's
what keeps the site honest about its own status.

## C. Technical credentials needed to finish the live Preview

Not documents — actual account setup, still pending:

1. Stripe test-mode API keys
2. Resend account + API key + verified sender domain/email
3. Upstash (or compatible) Redis REST URL + token
4. Preview environment variables pasted into Vercel (exact names in
   `handoff/02_VERCEL/PREVIEW_ENVIRONMENT_MATRIX.csv`)
5. IONOS DNS access, only once a real domain is ready to connect

## D. Professional review — not a document, an actual person

1. **Trademark/business attorney** — runs or confirms the name-clearance
   searches, reviews every ChatGPT-drafted legal document before it's
   final.
2. **CPA** — validates tax and bookkeeping treatment (sales tax,
   deposits/deferred revenue, milestone recognition, Stripe fees/refunds,
   contractor reporting, travel, estimated taxes).
