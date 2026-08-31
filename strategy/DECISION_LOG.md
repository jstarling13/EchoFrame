# Decision Log

**Purpose:** Record decisions that drive cross-file consistency

**Version:** 1.0 | **Date:** 2026-08-28

## Company name (2026-08-29, corrected 2026-08-29, elevated 2026-08-31)

**White Oak Operations is the selected working company name, pending
trademark, entity-name, domain, and common-law clearance — and, as of a
2026-08-31 preliminary search, a potential name conflict has actually
been identified, not just an unrun check.** An existing business
operating under the exact name "White Oak Operations" was found
offering virtual assistance, administrative support, business systems,
and workflow support — services close enough to overlap with this
business. Separately, and regardless of how the trademark question
resolves, `whiteoakoperations.com` is already registered by an
unrelated third party (GoDaddy, privacy-protected, registered
2024-10-08) and is not available. Full preliminary findings:
`handoff/04_NAME_LEGAL/NAME_CLEARANCE_WORKBOOK.csv`. This search was
non-authoritative (ChatGPT, with several registry checks incomplete due
to access restrictions) and does not substitute for a trademark
attorney's opinion — but it raises the real possibility that the name
needs to change before further investment, and should go in front of
counsel promptly rather than being treated as a routine formality. It
replaces
the "Practical AI Operations" working label used throughout the original
v1 package and is applied across the website (`website/`),
naming/positioning docs (`brand/NAMING_FRAMEWORK.md`,
`strategy/MARKET_POSITIONING.md`, `strategy/README.md`), and the
client-project ID convention (`operations/CRM_AND_FOLDER_SPEC.md`:
`WOO-YYYY-NNN`, was `PAO-YYYY-NNN`) — none of that usage should be
undone. It does **not** resolve `strategy/OPEN_QUESTIONS.md` item 1;
that item remains open until trademark, entity-name, domain, and
common-law clearance are each separately confirmed. The legal entity
name (which may differ from this working/trade name) is a distinct open
item — see `OPEN_QUESTIONS.md` item 2.

## Approved v1 architecture

- **O1**: Workflow Opportunity Diagnostic at $2,500; deposit $2,500; 10 business days.
- **O2**: Workflow Build Sprint at $7,500; deposit $3,750; 4 weeks.
- **O3**: AI Operations Transformation at $18,000; deposit $7,200; 8-10 weeks.
- **O4**: Enterprise AI Operations Program at $45,000; deposit $13,500; 16-20 weeks.
- **O5**: Workflow Assurance & Enablement at $2,500; deposit $2,500; Monthly; 3-month initial term.

## Positioning

Category: AI Operations Enablement. Promise: convert repeatable knowledge work into governed, tested workflows that the client can operate and improve. Differentiator: consulting + implementation + role-based training + ownership transfer.

## Go-to-market

Referral-first New York entry. Prioritize accounting, commercial real estate/property management, construction services, recruiting/staffing, and established professional services. Delay highly regulated autonomous decision use cases.

## Payment rules

Deposits are non-refundable once reserved work or discovery begins, subject to contract and applicable law. Change requests require written approval. Late invoices pause work after notice. Travel outside the agreed local radius is pre-approved and passed through at cost unless fixed in the SOW.

## Technical

Use Stripe-hosted payment surfaces initially. Store no card data. Use server-side webhook verification and idempotent event processing. Preserve IONOS email-related DNS records when connecting Vercel.
