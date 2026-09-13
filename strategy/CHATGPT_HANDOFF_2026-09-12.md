# EchoFrame (AI Consulting Practice) — ChatGPT Handoff Package

Prepared 2026-09-12. This is a complete context dump of Jacob's personal AI
consulting/implementation business for handing work to ChatGPT. It draws on
the project files in `/Users/jacob/AI-Consulting-Business` and the working
session that produced the current website. It does NOT include, and should
NOT be cross-referenced against, Magnolia Grove Consultants (MGC) — a
separate company Jacob works for that is unrelated to this business.

Anything not directly evidenced in files or conversation is marked
**UNKNOWN**. Nothing here should be treated as legal, tax, or trademark
advice — several items explicitly still need a licensed professional.

---

## 1. Identify the Business

- **Current business name:** EchoFrame
- **Previous names:** "Practical AI Operations" (original working label in
  the v1 package) → "White Oak Operations" (adopted 2026-08-29, used
  throughout the codebase/docs until this session) → **EchoFrame** (adopted
  2026-09-12, current).
- **Is the name finalized:** No. "White Oak Operations" was dropped after a
  preliminary (non-authoritative) name-clearance search found a likely
  conflict: an existing business already operates under that exact name
  offering overlapping services, and `whiteoakoperations.com` was already
  registered by an unrelated third party. See
  `handoff/04_NAME_LEGAL/NAME_CLEARANCE_WORKBOOK.csv` and
  `strategy/DECISION_LOG.md` for that dead end. EchoFrame itself has **not**
  been run through an equivalent trademark/entity-name/domain clearance in
  this repo — that is an open task, not a completed one.
- **Website/domain:** A Next.js site exists locally at
  `AI-Consulting-Business/website`, currently only running on
  `localhost:3000` in dev. It is **not deployed**. A prior session's notes
  (`handoff/00_READ_ME_FIRST/CURRENT_STATE.md`) record that Vercel project
  creation was blocked (403 error) under a Vercel team literally named
  **"EchoFrame's projects"** — meaning an EchoFrame-branded Vercel team
  already existed before this session. The actual registered domain string
  for EchoFrame is **UNKNOWN** to Claude — Jacob has said he wants to reuse
  an existing EchoFrame domain so he doesn't have to buy a new one, but the
  literal domain name was never stated in this conversation. Check the old
  EchoFrame project's `vercel.json`/DNS registrar (IONOS, per prior docs)
  for the actual domain.
- **Geographic market:** Primarily the Northeast U.S., especially the New
  York City area (Queens specifically named), driven by a referral pipeline
  through Jacob's aunt, who works as a bookkeeper there. Jacob himself is
  based in the Southeast (mailing address on file: 17 Ridgeway Drive,
  Cataula, GA 31804 — near Columbus, GA). Work is remote-first with
  onsite/travel trips billed separately.
- **Founder:** Jacob Starling. M.S. in Finance, Emory University. Entering
  the U.S. Navy as a Supply Corps officer (logistics/contracting/financial
  management). This consulting practice is explicitly a way to keep hands-on
  with the newest AI models, make money, and keep learning before he ships
  out — that framing has not been hidden from the public site (the About
  page already discloses the Navy commission).
- **Legal/business structure:** **UNKNOWN / not finalized.** Every page that
  touches it (About, Terms, Privacy) explicitly states legal entity type,
  formation state, and registered agent are still pending and are
  intentionally left blank rather than fabricated.
- **Current stage:** Pre-launch. Website built and passing its own test
  suite (72 tests) locally; not deployed; no confirmed live clients through
  this specific EchoFrame-branded practice yet (one real prospect/client
  narrative exists — the Dr. Hendizadeh proposal and the bookkeeper case
  study — see Section 29). No legal entity, no live payment processing
  connected to the new pricing model.
- **What the business currently does (as positioned on the live site):**
  Hands-on AI consulting and workflow automation for small businesses —
  bookkeeping/financial workflow automation, general process automation,
  multi-entity tracking, customer communication automation, reporting
  dashboards, staff training, systems/security review, and ongoing AI
  consulting — delivered personally by Jacob, billed hourly.
- **What Jacob originally intended it to do:** The original package (built
  before this session, under "White Oak Operations") positioned this as
  **"AI Operations Enablement"** — a founder-led consultancy for
  established businesses (10-250 employees) offering five fixed-price,
  tiered engagements (a diagnostic, a build sprint, a transformation
  program, an enterprise program, and a monthly assurance retainer),
  ranging $2,500-$45,000, sold nationally with an initial New York
  go-to-market focus.
- **What he is now repositioning it to do:** A single, simple hourly
  engagement model ($40/hour + a travel fee + a daily onsite food stipend,
  no fixed packages, no public checkout, everything quoted individually
  after a conversation) under the EchoFrame name, marketed with a broader,
  named list of service capabilities rather than five priced tiers, aimed
  more directly at small businesses (not necessarily the 10-250-employee
  band from the original strategy docs) reachable through his aunt's
  bookkeeping client network in Queens/NYC.
- **Why the repositioning is happening:**
  1. He wants to reuse an EchoFrame domain/brand he already owns instead of
     clearing and buying a new one for "White Oak Operations" (which also
     had a real name-conflict problem).
  2. Real client work he's actually quoting (see the Dr. Hendizadeh
     proposal, Section 29) is billed hourly + travel + per diem, not in
     fixed tiers — the pricing model changed to match how he actually
     sells.
  3. He explicitly does not want "too many products," a lesson drawn from
     his prior EchoFrame venture, which had a fragmented multi-product
     catalog (RateWatch, AutoLedger, CallRouter, QuoteRevive, ShiftLens,
     etc. — see Section 5) that he does not want to repeat.
  4. He wants a "modern corporate" visual/verbal register (his words:
     "like BCG, Deloitte, Bain") rather than the more generic consulting
     template voice the original package used.
  5. He wants the positioning to explicitly help/augment bookkeepers and
     CPAs (via automation that frees their time/capacity) rather than
     read as replacing or competing with them — this came directly from
     the real story of automating his aunt's bookkeeping workload so she
     could take on more clients.
- **What has changed in his thinking:** Moved from "abstract enterprise AI
  operations consultancy with tiered productized packages" toward "one
  named consultant, one simple hourly rate, a broad menu of practical
  services, personal story front-and-center, reusing an existing brand,"
  while still wanting the finished product to *read* as polished/corporate
  rather than boutique-casual.

---

## 2. Current Positioning

**FINAL / APPROVED**
- Billing model: hourly ($40/hr) + travel fee (quoted per trip) + $50/day
  onsite food stipend. No fixed packages. No public checkout — every
  project is quoted after a conversation.
- Brand name: EchoFrame (reusing the existing brand/domain, not building a
  new one).
- Explicit non-goal: do not position as replacing bookkeepers/CPAs; position
  as giving them automation/capacity so they can serve more clients with
  less manual work and fewer errors.
- Do not delete or discard the old "White Oak Operations" / O1-O5 package
  materials or Stripe integration code — they stay in the repo, unused,
  as historical/superseded material.

**CURRENT DIRECTION** (built this session, reflects Jacob's stated
preferences, but not necessarily "locked forever")
- Category mix: primarily **AI implementation/automation consulting** with
  a **bookkeeping/financial-operations** specialty lane (reflecting the
  aunt's-client pipeline), plus general **process automation** and
  **staff training**. Not positioned as pure strategy consulting, not
  positioned as a software/product company.
- Tone: confident, declarative, Title Case headlines, short "X meets Y" /
  tagline-style hero copy (explicitly modeled on the register of BCG/
  Bain/Deloitte homepages, without borrowing their actual content or
  claiming a firm's scale) — combined with a personal, named-founder
  story (not an anonymous "we" institution).
- Value proposition (as written on the live site): "EchoFrame brings
  hands-on AI and workflow automation to small businesses across the
  Northeast — scoped to the operation as it actually runs, built to be
  owned, and backed by continuous command of the newest models as they
  ship."
- Differentiator vs. generic AI agencies (as written): one dedicated
  consultant who shows up and stays current on newest models/tools, not a
  call center or reseller; the client ends up owning and able to extend
  what's built, not dependent on the vendor indefinitely; billing is
  transparent and hourly, not opaque productized pricing.

**PROPOSED / IN TENSION — needs a decision**
- Ideal client size: the *original* strategy docs (pre-this-session) define
  the ICP as established businesses, 10-250 employees. The *new* direction
  (this session) leans toward smaller businesses reachable through a
  bookkeeper's referral network (likely much smaller than 10-250
  employees — solo practices, small retail, small professional
  practices). **These two ICP definitions have not been reconciled.**
- Visual palette: the logo is navy + gold on a transparent background
  (from the real EchoFrame brand asset). The live site's header/nav still
  uses an inherited powder-blue/periwinkle color scheme from the old
  "White Oak Operations" design system. Jacob has said he loves the
  powder blue and is still deciding the final palette, and does not want
  colors changed again yet. So: **logo colors (navy/gold) and site chrome
  color (powder blue) are currently not unified, and that is intentional
  and paused, not an oversight.**
- Tone tension: "modern corporate, BCG-style" vs. an earlier stated desire
  for "Southern charm" warmth in the copy. The current site blends these
  (confident tagline headlines + a warm, personal founder story) but this
  blend has not been explicitly signed off as final.

**UNRESOLVED**
- Whether pricing (the $40/hr rate and the ~$1,250 example travel fee) is
  meant to be shown publicly on the website at all, or should be pulled
  behind a "request a quote" wall with no numbers shown. It is currently
  shown publicly on `/` and `/services`.
- Exact travel radius/base and how travel fee is actually calculated
  (currently just described qualitatively as "quoted per trip, ~$1,250
  typical for a single-day regional trip").
- Whether EchoFrame's name/domain/trademark has any conflicts (never
  checked, unlike the old "White Oak Operations" name which WAS checked
  and found conflicted).

**CLAUDE RECOMMENDATION** (not a decision Jacob has made — flagging for
ChatGPT/Jacob to actually decide)
- Reconcile the ICP question explicitly before writing more sales/ICP
  material: either (a) formally narrow the ICP to smaller referral-driven
  small businesses and rewrite `strategy/ICP_PERSONAS_AND_TRIGGERS.md`
  accordingly, or (b) keep the original 10-250 employee ICP for larger
  future work and treat the bookkeeper/small-business channel as a
  separate, smaller lane. Trying to serve both without saying so risks
  incoherent marketing.

---

## 3. My Goals for the Business

- **Short-term goal (explicit):** Get the EchoFrame-branded site and
  pricing model to a state Jacob is happy showing to real prospects,
  starting with warm referrals via his aunt's bookkeeping clients in
  Queens/NYC.
- **3/6/12-month goals:** **UNKNOWN** — not discussed in dollar or client-
  count terms this session. The *original* (superseded) 30/60/90-day plan
  in `strategy/30_60_90_DAY_PLAN.md` targeted: two paid design partners
  and a rehearsed diagnostic in the first 30 days; first delivered
  engagements and five referral partnerships by day 60; conversion to
  larger/retainer work and 10 qualified introductions/month by day 90 —
  but that plan was written for the old five-tier package model and has
  not been re-confirmed under the new hourly model.
- **Revenue goals:** **UNKNOWN** — no explicit revenue target given.
- **Desired client volume / project size:** **UNKNOWN** in specific
  numbers. Directionally: smaller, more numerous, referral-sourced small-
  business engagements rather than large enterprise programs, at least for
  the current phase.
- **Desired recurring revenue:** An "Ongoing AI Consulting" service exists
  in the current catalog (month-to-month, hourly) as the intended
  recurring-revenue lane, but no target dollar amount or attach rate has
  been set.
- **Desired service mix:** Broad-but-shallow: bookkeeping/financial
  workflow automation, general process automation, multi-entity tracking,
  customer communication automation, reporting/dashboards, staff training,
  security review, ongoing consulting — one hourly rate applies to all of
  it (see Section 14).
- **Employees/contractors vs. AI-assisted solo delivery:** Currently solo.
  Every public-facing page emphasizes "one consultant, not a call center."
  No stated plan to hire yet.
- **Personal involvement in delivery:** Fully hands-on/personal — this is
  explicitly part of the pitch, not incidental.
- **Boutique vs. scale:** Currently boutique/solo by explicit design choice
  and by circumstance (Jacob is about to enter active-duty Navy service).
  Long-term scale intentions beyond that: **UNKNOWN.**
- **Local/regional/national/remote:** Remote-first, with paid travel for
  onsite work; go-to-market focus is regional (Northeast/NYC), not
  strictly local, not yet national.
- **Long-term vision:** **UNKNOWN** beyond "keep learning and applying the
  newest AI models, fund himself, stay hands-on with real client work"
  through the period before/alongside military service.

---

## 4. Complete Decision Log

| Decision | Status | Why | Context | What ChatGPT should NOT reconsider |
|---|---|---|---|---|
| Business is EchoFrame, not "White Oak Operations" | **Final** | Reuse an existing domain/brand instead of clearing and buying a new one; "White Oak Operations" had a real name conflict found in prior research | Old name/docs remain in the repo as superseded, not deleted | Don't revert to "White Oak Operations" as the active brand |
| Billing model = hourly $40/hr + travel fee + $50/day onsite food stipend | **Final** | Matches how Jacob actually bills real client work (see Dr. Hendizadeh proposal); simpler to sell | Travel fee is quoted per trip, not fixed; ~$1,250 used as a representative example for a single-day regional trip | Don't reintroduce fixed $2,500-$45,000 tiered packages as the active model |
| No public checkout / no self-serve payment | **Final** | Every engagement is scoped individually; this was already the design philosophy under the old brand too (see `website/docs/NO_PUBLIC_CHECKOUT.md`) | Old Stripe checkout code still exists in the repo, dormant, untouched | Don't add a "buy now" button |
| Do not delete any existing files, code, or business docs | **Final** | Explicit, repeated instruction from Jacob | Superseded docs get a note at the top marking them superseded, not removed | Don't recommend deleting the old O1-O5 package files, Stripe code, or old EchoFrame venture files |
| Old EchoFrame venture (RateWatch, AutoLedger, etc.) stays fully separate and untouched | **Final** | It's a distinct, complete prior business Jacob wants preserved as-is | Lives at the real iCloud "EchoFrame" folder and a duplicate "EchoFrame copy" folder; only the brand name/logo assets were reused, nothing else | Don't merge, reference, or promote old EchoFrame products on the new site unless Jacob explicitly asks |
| Positioning: assist/augment bookkeepers & CPAs, not replace them | **Final** | Came directly from the real story of automating his aunt's bookkeeping workload to free her time for more clients | Applies to case-study language and general marketing framing | Don't write copy implying automation displaces bookkeepers/accountants |
| Use the real EchoFrame logo asset, not an invented one | **Final** | Jacob explicitly rejected a hand-drawn recreation once the real file was found | Real files: `.../EchoFrame/site/echoframe-logo.png` (full lockup) and `echoframe-icon.png` (icon only) | Don't recreate/redesign the logo without being asked |
| Don't change the site color palette yet | **Final (for now)** | Jacob loves the current powder blue and is still deciding the palette | Logo's native colors (navy/gold) exist as CSS variables but are not yet applied site-wide | Don't repaint the header/chrome to navy or any other scheme without explicit sign-off |
| Copy tone: confident/"modern corporate" (BCG/Bain/Deloitte-style), Title Case headlines | **Final direction, wording itself still editable** | Explicit request; prior copy was judged too casual/"AI blog"-sounding | Applied to homepage, services, about hero copy already | Don't revert to the more casual "someone who shows up" register |
| Client email is jacob.starling@echoframe.net | **Final** | Explicit instruction | Replaces jacobstarling4313@gmail.com across the public site | — |
| ICP = established 10-250 employee businesses | **Superseded / unresolved**, see Section 2 | Was the original strategy | Newer direction leans smaller/referral-based | ChatGPT should help resolve this, not assume either answer |
| Legal entity type / formation state / registered agent | **Not decided** | Owner-level decision pending | Every legal page already says so explicitly | Don't fabricate an entity type or state |

---

## 5. Everything Already Created

All paths are relative to `/Users/jacob/AI-Consulting-Business` unless noted.

| Asset | What it is | Purpose | Location | Status |
|---|---|---|---|---|
| Live website (Next.js app) | Full marketing site: home, services, about, method, industries, training, security, contact, privacy, terms, thank-you | Public-facing site | `website/` | Functional locally, not deployed, rebranded to EchoFrame this session |
| Hourly pricing model | `HOURLY_RATE_USD`, travel fee copy, `$50`/day stipend, 9-item service catalog | Drives the live pricing/services UI | `website/lib/services.ts` | Complete, live |
| Old fixed-package pricing model | 5 offers (O1-O5), Stripe milestone logic | Was the old commercial model | `website/lib/offers.ts` | Superseded, untouched, still present |
| Stripe checkout/webhook integration | Private payment-link generator + webhook handler for the old O1-O5 model | Was meant for staff-sent private payment links, never public | `website/lib/stripe.ts`, `website/app/api/stripe/*` | Dormant/unused under the new model, not deleted |
| Business Blueprint | Mission, business model, category, operating loop, moat, success metrics | Foundational strategy doc | `strategy/BUSINESS_BLUEPRINT.md` | Written under the old "AI Operations Enablement" framing; not yet revised for the new hourly/EchoFrame direction |
| Market Positioning | Old positioning statement, value pillars, proof standard | Strategy | `strategy/MARKET_POSITIONING.md` | Still says "White Oak Operations" — **needs updating** |
| ICP/Personas/Triggers | Ideal company profile, personas, pains, buying triggers, disqualifiers | Sales targeting | `strategy/ICP_PERSONAS_AND_TRIGGERS.md` | Reflects the OLD 10-250 employee ICP — see Section 2 tension |
| Industry Priorities | Wave 1/Wave 2 verticals, industries to delay/gate | GTM sequencing | `strategy/INDUSTRY_PRIORITIES.md` | Not reconciled with the bookkeeping/small-business pivot |
| Positioning Architecture | Category line, promise, mechanism, evidence, guardrails, CTA ladder | Messaging consistency | `strategy/POSITIONING_ARCHITECTURE.md` | Old framing, not updated |
| Decision Log | Historical record of naming/pricing/positioning decisions through 2026-08-31 | Institutional memory | `strategy/DECISION_LOG.md` | Accurate history, does not yet include this session's EchoFrame pivot |
| Assumptions | Business/commercial/technology/risk/economics assumptions | Guardrails | `strategy/ASSUMPTIONS.md` | Old-model assumptions (e.g., O1-O5 payment splits) |
| Open Questions | Owner-level unresolved items (name, address, travel radius, vendors) | Tracks what's genuinely undecided | `strategy/OPEN_QUESTIONS.md` | Partially stale (name question was about "White Oak," now moot) |
| 30/60/90-Day Plan | Launch sequencing | Old GTM plan | `strategy/30_60_90_DAY_PLAN.md` | Written for the old package model; not reconfirmed |
| Competitive Alternatives & Objections | Alternatives clients consider, objection-response frames | Sales enablement | `strategy/COMPETITIVE_ALTERNATIVES_AND_OBJECTIONS.md` | Generically still usable, not EchoFrame-specific |
| Offer Catalog (old) | Full scope/price/deliverables for O1-O5 | Old sales reference | `sales/OFFER_CATALOG.md` | Marked superseded (note added this session), kept for reference |
| Hourly Pricing Model (new) | Current $40/hr + travel + stipend + service list, written to mirror `website/lib/services.ts` | New sales/pricing reference | `sales/HOURLY_PRICING_MODEL.md` | **Created this session**, current source of truth for pricing |
| Service Descriptions (old) | Plain-language descriptions of the 5 old offers | Old marketing reference | `brand/SERVICE_DESCRIPTIONS.md` | Marked superseded this session |
| Pricing Workbook | Spreadsheet version of old pricing | Internal reference | `sales/PRICING_WORKBOOK.xlsx` | Reflects old model, not regenerated for hourly model |
| Travel Economics | Formula/gate for approving travel, client travel terms | Internal ops reference | `sales/TRAVEL_ECONOMICS.md` | Still generically usable; "actual reasonable cost" travel policy is consistent with the new travel-fee model |
| Discovery Script & Questionnaire | Sales discovery questions | Sales asset | `sales/DISCOVERY_SCRIPT_AND_QUESTIONNAIRE.md` | **Not reviewed this session** — likely still usable, needs a read-through |
| Sales Pipeline, Objection/Close Playbook, Proposal & Scope Template, Outreach/Intro Scripts, Email & Referral Library, Sales Checklists, NY Market Entry | Sales system documents | Sales enablement | `sales/*.md` | **Not reviewed this session** — exist, contents not verified against new model |
| Naming Framework, Messaging Toolkit, Brand Voice & Terminology | Brand strategy docs | Brand system | `brand/*.md` | **Not reviewed this session**; likely reference "White Oak Operations" and need updating |
| Client Delivery templates (intake, interviews, workflow maps, ROI assessment, SOPs, prompt library, handoff packages, etc.) | Full client-engagement document set | Delivery methodology | `client-delivery/*.md` (21 files) | **Not reviewed this session** — appears to be a complete, reusable delivery framework independent of the pricing model |
| Training system (owner/manager/employee training, advanced workflow training, cheat sheets, model selection framework, workflow economics, data/human-review escalation) | Training curricula | Client & internal training | `training/*.md` (9 files) | **Not reviewed this session** |
| Security docs (AI acceptable use, PII/PHI/financial guidance, access/MFA, data classification, approved tool framework, offboarding, security review checklist) | Security/governance policy set | Governance | `security/*.md` (8 files) | **Not reviewed this session** — likely solid, generic content |
| Legal drafts (MSA, NDA, DPA, ToS, Privacy, cancellation/refund, travel expense policy, SOW templates per O1-O5) | Attorney-review-required legal drafts | Legal | `legal/*.md` (13 files) | Explicitly drafts, not attorney-approved; SOW templates are keyed to the OLD offer codes and need rework for hourly billing |
| Operating Manual, SOPs, CRM & Folder Spec | Internal operations | Ops | `operations/*.md` | **Not reviewed this session** |
| Financial Model, ROI Model (spreadsheets) | Financial planning tools | Finance | `finance/*.xlsx` | **Not reviewed this session** — likely built for the old package model |
| Handoff package (00-07 numbered folders: GitHub, Vercel, external services, name/legal, QA, production, tracking) | A prior, very detailed Claude-execution handoff for deploying the original White Oak Operations site | Deployment runbook | `handoff/` | Predates this session; describes a blocked Vercel deployment under a team called "EchoFrame's projects" |
| Archive (polished .docx/.pdf artifacts, original Claude implementation brief, original Stripe package) | Historical/polished versions of the above documents | Historical record | `archive/` | Explicitly archival, not current |
| Real client proposal | "Financial Workflow Consulting Proposal" for Dr. Pedy Hendizadeh — hourly $40/hr + $1,250 flat travel fee model, add-on modules with flat base fees | The actual real-world pricing precedent that drove this session's pivot | `/Users/jacob/Plan for Dr. Hendizadeh.pdf` (outside the repo) | Real, in-progress/delivered client proposal |

---

## 6. Current File Inventory (highest-value files for ChatGPT)

| File | Type | Purpose | Current? | Approved info? | ChatGPT should see it | Upload to ChatGPT | Claude still needs it |
|---|---|---|---|---|---|---|---|
| `sales/HOURLY_PRICING_MODEL.md` | Markdown | Current pricing/services source of truth | Yes | Yes | Yes | Yes | Yes (mirrors website code) |
| `website/lib/services.ts` | TypeScript | Actual code defining live pricing/services | Yes | Yes | Optional (ChatGPT doesn't need code, just the facts in the .md above) | No | Yes |
| `strategy/DECISION_LOG.md` | Markdown | History of naming/pricing decisions | Partially (predates EchoFrame rename) | Yes, as history | Yes | Yes | Yes |
| `strategy/ICP_PERSONAS_AND_TRIGGERS.md` | Markdown | Old ICP definition | Stale vs. new direction | Historically yes | Yes, to work the reconciliation | Yes | Maybe |
| `strategy/MARKET_POSITIONING.md`, `POSITIONING_ARCHITECTURE.md`, `BUSINESS_BLUEPRINT.md` | Markdown | Old strategic framing | Stale (still say "White Oak Operations") | Partially | Yes, as raw material to revise | Yes | Maybe |
| `sales/OFFER_CATALOG.md`, `brand/SERVICE_DESCRIPTIONS.md` | Markdown | Old 5-tier pricing/services | Superseded (marked) | Historical only | Only if useful as a reference for what NOT to do | Optional | No |
| `Plan for Dr. Hendizadeh.pdf` | PDF | Real client proposal that set the new pricing precedent | Yes | Yes | Yes — this is the best single reference for how real engagements should be scoped/worded | Yes | No |
| `client-delivery/*.md` (21 files) | Markdown | Full delivery methodology (intake, workflow maps, ROI, SOPs, training, handoff) | Likely still usable, unreviewed this session | Unconfirmed | Yes, high value — ChatGPT can adapt these to the hourly model | Yes | Maybe |
| `legal/*.md` (13 files) | Markdown | MSA/NDA/DPA/ToS/Privacy/SOW drafts | Attorney-review-required; SOW templates keyed to old O1-O5 codes | No (drafts only) | Only for structure, not for legal advice | Optional | Yes, until replaced |
| `security/*.md` (8 files) | Markdown | Governance/security policy | Likely still generically valid | Unconfirmed | Yes | Optional | Maybe |
| `handoff/00_READ_ME_FIRST/CURRENT_STATE.md`, `OWNER_DECISIONS.md` | Markdown | Deployment status, what's blocked, what's owner-controlled | Predates this session but factually still true (site not deployed) | Yes | Yes | Yes | Yes |
| Website source (`website/app`, `website/components`, `website/lib`) | Code | The actual implemented site | Yes | Yes | No (ChatGPT can't run/deploy it) | No | Yes — stays with Claude |

---

## 7. Active Workstreams

### Workstream: EchoFrame rebrand of the website
- **Objective:** Replace "White Oak Operations" branding with EchoFrame across the live site.
- **Status:** Done for text/brand name, logo, favicon, email. Color palette intentionally left unchanged.
- **Completed:** Logo/icon swapped to the real EchoFrame assets; brand name replaced site-wide; email updated; copy tone elevated on home/services/about.
- **Remaining:** Nothing blocking; palette decision is open but explicitly paused by Jacob.
- **Blockers:** None active — palette is a "waiting on Jacob," not a blocker.
- **Dependencies:** None.
- **Files:** `website/components/Header.tsx`, `Footer.tsx`, `app/*/page.tsx`, `app/globals.css`, `public/images/echoframe-logo.png`, `app/icon.png`.
- **Next step:** Await Jacob's final palette decision.
- **Best owner:** Claude (implementation is code/CSS in a live dev server).
- **Why:** Requires direct file edits and browser verification Claude already has set up.

### Workstream: New hourly pricing model
- **Objective:** Replace the 5 fixed packages with $40/hr + travel + stipend, no checkout.
- **Status:** Complete and live on the website; mirrored into `sales/HOURLY_PRICING_MODEL.md`.
- **Completed:** `lib/services.ts`, `PricingModel.tsx`, `ServicesGrid.tsx`, homepage/services page updated, old model left untouched/unlinked.
- **Remaining:** Reconcile with `sales/PRICING_WORKBOOK.xlsx` (still shows old numbers) and `finance/ROI_MODEL.xlsx`/`FINANCIAL_MODEL.xlsx` (unreviewed, likely stale).
- **Blockers:** None.
- **Dependencies:** None.
- **Files:** as listed in Section 6.
- **Next step:** Decide whether to regenerate the financial model spreadsheets for the hourly model — good ChatGPT task (see Section 9).
- **Best owner:** Split — ChatGPT can rebuild the financial-model logic/content; Claude would need to actually edit the .xlsx file if requested.

### Workstream: Positioning/ICP reconciliation
- **Objective:** Resolve whether the ICP is the old 10-250-employee "established business" profile or the new smaller-business/bookkeeper-referral profile.
- **Status:** Unresolved, flagged, not started.
- **Completed:** Nothing yet — just identified as a gap in this handoff.
- **Remaining:** A real decision, then a rewrite of `strategy/ICP_PERSONAS_AND_TRIGGERS.md`, `INDUSTRY_PRIORITIES.md`, and homepage copy if it changes.
- **Blockers:** Needs Jacob's decision.
- **Dependencies:** None.
- **Files:** `strategy/ICP_PERSONAS_AND_TRIGGERS.md`, `strategy/INDUSTRY_PRIORITIES.md`.
- **Next step:** Jacob decides; ChatGPT drafts the revised ICP doc.
- **Best owner:** ChatGPT (pure strategy writing, no code).
- **Why:** No file-system or deployment dependency.

### Workstream: Deployment (Vercel/domain/DNS)
- **Objective:** Get the site live on the real EchoFrame domain.
- **Status:** Blocked as of the last recorded attempt (403 creating a Vercel project under team "EchoFrame's projects"); not re-attempted this session.
- **Completed:** Local dev site fully functional; `.claude/launch.json` configured for local preview only.
- **Remaining:** Resolve Vercel access/team issue; connect Git remote (none exists per prior notes); configure environment variables; point DNS.
- **Blockers:** Vercel account/team access; unknown current Git remote status.
- **Dependencies:** Jacob's Vercel/GitHub/IONOS access.
- **Files:** `handoff/02_VERCEL/*`, `handoff/01_GITHUB/*`, `handoff/06_PRODUCTION/*`.
- **Next step:** Jacob checks Vercel team access and the actual EchoFrame domain/DNS setup.
- **Best owner:** Claude, once Jacob unblocks account access — this is hands-on-keyboard/browser work.
- **Why:** Requires actual deployment execution, not strategy.

### Workstream: Legal docs rework for hourly model
- **Objective:** Update MSA/SOW/ToS/Privacy/cancellation drafts to reflect hourly billing instead of O1-O5 fixed packages.
- **Status:** Not started.
- **Completed:** None.
- **Remaining:** Full rewrite of SOW templates at minimum; ToS/Privacy need lighter edits (they already reference "if you pay online" caveats generically).
- **Blockers:** These are drafts pending actual attorney review regardless of content — do not treat any rewrite as final.
- **Dependencies:** None to start drafting; attorney review before real use.
- **Files:** `legal/*.md`.
- **Next step:** Draft revised SOW template for hourly billing.
- **Best owner:** ChatGPT for the first draft; a real attorney before use.
- **Why:** Pure drafting, no code/deployment involved.

---

## 8. What Claude Is Currently Doing

- **Active/most recent tasks:** Rebranding the website to EchoFrame (logo, copy tone, email); building the new hourly pricing model into the live site; producing this handoff document.
- **Awaiting approval:** The final color palette (paused, not blocking).
- **Partially completed:** None outstanding from this session — the rebrand and pricing-model swap are both functionally complete and tested.
- **Queued:** Nothing explicitly queued beyond what Jacob asks next.
- **Agent-based/research/coding/website/automation/file work:** All of this session's work was direct file editing + a live browser preview (Next.js dev server) to verify changes, plus filesystem search to locate the real EchoFrame brand assets. No sub-agents were spawned. No Cowork sessions were used.
- **Recommendation per task:**
  - Website rebrand/pricing implementation → **stayed in Claude** (correct — needed file edits + live verification).
  - This handoff document → **Claude**, now handing off.
  - Everything in Section 9 below → **should move to ChatGPT.**

---

## 9. Tasks ChatGPT Can Take Over Immediately

1. **TASK:** Reconcile the ICP (10-250 employee "established business" vs. smaller referral-driven small business).
   **WHY CHATGPT IS SUFFICIENT:** Pure strategic reasoning/writing, no code or file-system dependency.
   **INPUTS NEEDED:** Section 2 and 7 of this doc; `strategy/ICP_PERSONAS_AND_TRIGGERS.md` and `INDUSTRY_PRIORITIES.md` content (summarized above; full text can be pasted in if needed).
   **EXISTING WORK TO USE:** The old ICP doc as a starting point to revise, not discard.
   **DECISIONS TO PRESERVE:** Hourly pricing model; no-checkout policy; assist-not-replace-bookkeepers positioning.
   **EXPECTED OUTPUT:** A revised ICP/persona document reconciling both audiences (or an explicit decision to serve one primarily).
   **PRIORITY:** High.
   **CLAUDE USAGE SAVED:** Moderate. **TYPE:** context/tokens.

2. **TASK:** Rewrite `strategy/MARKET_POSITIONING.md`, `POSITIONING_ARCHITECTURE.md`, and `BUSINESS_BLUEPRINT.md` to reflect EchoFrame + hourly model instead of "White Oak Operations" + O1-O5.
   **WHY:** Pure document editing/strategy writing.
   **INPUTS:** Current text of those files (see Section 5) + Sections 1-4 of this handoff.
   **EXISTING WORK TO USE:** Keep the underlying strategic logic (operating loop, moat, value pillars); just update the vehicle (name, pricing, ICP language).
   **DECISIONS TO PRESERVE:** All FINAL items in Section 4.
   **EXPECTED OUTPUT:** Three revised markdown documents Jacob can drop back into `strategy/`.
   **PRIORITY:** High. **CLAUDE USAGE SAVED:** Moderate. **TYPE:** context/tokens.

3. **TASK:** Draft a revised SOW/proposal template for hourly billing (replacing the O1-O5-keyed SOW templates).
   **WHY:** Drafting work; the real Dr. Hendizadeh proposal is an excellent model to generalize from.
   **INPUTS:** `Plan for Dr. Hendizadeh.pdf` content (already summarized in Section 29), `sales/HOURLY_PRICING_MODEL.md`.
   **EXISTING WORK TO USE:** `legal/sow-template-*.md` structure, `sales/PROPOSAL_AND_SCOPE_TEMPLATE.md`.
   **DECISIONS TO PRESERVE:** $40/hr, travel fee quoted per trip, $50/day stipend, no fixed packages.
   **EXPECTED OUTPUT:** A generalized SOW/proposal template usable for any client.
   **PRIORITY:** High. **CLAUDE USAGE SAVED:** High. **TYPE:** context/tokens/file work.

4. **TASK:** Rebuild the financial/ROI model spreadIt logic for hourly billing (conceptually — actual .xlsx editing may need a spreadsheet tool).
   **WHY:** Modeling/spreadsheet logic can be fully specified by ChatGPT; only the final file format touch may need another tool.
   **INPUTS:** `finance/FINANCIAL_MODEL.xlsx` and `ROI_MODEL.xlsx` contents (unreviewed this session — pull before starting), `sales/HOURLY_PRICING_MODEL.md`.
   **DECISIONS TO PRESERVE:** Hourly rate, travel fee, stipend.
   **EXPECTED OUTPUT:** Updated formulas/assumptions ready to paste into a spreadsheet.
   **PRIORITY:** Medium. **CLAUDE USAGE SAVED:** Moderate. **TYPE:** tokens.

5. **TASK:** Sales system pass — discovery script, objection/close playbook, outreach/referral messaging, cold email — rewritten for EchoFrame + hourly model + assist-the-bookkeeper positioning.
   **WHY:** Pure copywriting/strategy.
   **INPUTS:** Existing `sales/*.md` files (unreviewed this session, but titles/purpose known — see Section 5), Section 2-3 of this doc.
   **EXPECTED OUTPUT:** Updated sales scripts/messaging.
   **PRIORITY:** Medium-High. **CLAUDE USAGE SAVED:** High. **TYPE:** context/tokens.

6. **TASK:** Marketing content for the aunt/bookkeeper referral channel specifically — a short outreach sequence, referral-ask language, and a one-page explainer bookkeepers/CPAs could hand to their own clients.
   **WHY:** Pure copywriting, no implementation dependency.
   **INPUTS:** Section 1, 2, 29 of this doc (the real bookkeeper case study and the "assist, don't replace" positioning).
   **EXPECTED OUTPUT:** Referral-channel marketing kit.
   **PRIORITY:** High (this is Jacob's most concrete, real lead source right now). **CLAUDE USAGE SAVED:** High. **TYPE:** context/tokens.

7. **TASK:** Expand the service catalog (Jacob asked for "a complete catalog containing ideas of services we can provide" — not yet done).
   **WHY:** Brainstorming/ideation, no code needed to draft the list; Claude only needs to touch code once Jacob approves a final list.
   **INPUTS:** Current 9-item list in `website/lib/services.ts` / `sales/HOURLY_PRICING_MODEL.md`; Section 14 of this doc; the Dr. Hendizadeh plan's add-on-module structure as a style reference.
   **EXISTING WORK TO USE:** Don't lose the "not too many productized SKUs" constraint — this should read as an idea bank / expanded descriptions, not a return to priced packages.
   **EXPECTED OUTPUT:** An expanded, organized list of service ideas/descriptions Jacob can approve, which Claude then implements in code.
   **PRIORITY:** High (explicitly requested by Jacob, not yet delivered). **CLAUDE USAGE SAVED:** High. **TYPE:** context/tokens.

8. **TASK:** General brand voice/messaging toolkit rewrite (`brand/NAMING_FRAMEWORK.md`, `MESSAGING_TOOLKIT.md`, `BRAND_VOICE_AND_TERMINOLOGY.md`) for EchoFrame's BCG-inflected-but-personal tone.
   **WHY:** Pure writing.
   **INPUTS:** Section 2 of this doc (tone direction), current file contents (unreviewed this session).
   **EXPECTED OUTPUT:** Updated brand voice docs.
   **PRIORITY:** Medium. **CLAUDE USAGE SAVED:** Moderate. **TYPE:** context/tokens.

9. **TASK:** Competitive landscape research specific to small-business AI/automation consultants in the Northeast/NYC bookkeeping-adjacent space.
   **WHY:** Research/synthesis ChatGPT (with browsing) can do independently.
   **INPUTS:** Section 1-2 of this doc.
   **EXPECTED OUTPUT:** A competitive landscape brief.
   **PRIORITY:** Medium. **CLAUDE USAGE SAVED:** High (this would otherwise burn significant Claude research/browser time). **TYPE:** browser/context.

---

## 10. Tasks That Should Stay in Claude

- **Any further website code/copy changes and CSS/palette work.** Claude already has the repo open, a live dev server running, and verified test coverage (72 passing tests). Moving this to ChatGPT would mean re-establishing all of that context and losing direct verification.
- **Actual deployment (Vercel/DNS/domain connection).** Requires direct account/browser interaction Claude is set up to do (or explicitly blocked pending Jacob's access) — not something ChatGPT can execute.
- **Any edit to `website/lib/offers.ts`, Stripe integration, or test files.** These are working code with a passing test suite; edits need to happen in the codebase directly, and Claude already understands exactly why each piece was left untouched (see Section 4).
- **Verifying any new copy actually renders correctly** (spacing, responsive layout, accessibility) — this needs the live browser preview Claude has open.

**Why these stay:** Not because Claude "started" them, but because they require direct file-system access, a running dev server, and test verification that ChatGPT structurally cannot do.

---

## 11. Tasks That Should Be Split

### Service catalog expansion (see Section 9, task 7)
1. **ChatGPT:** Draft an expanded list/description bank of service ideas, organized by category, consistent with "not too many productized SKUs."
2. **Jacob:** Reviews and picks which ones to actually feature.
3. **Claude:** Implements the approved list into `website/lib/services.ts` and the services page.
4. **ChatGPT:** Reviews the live copy (Jacob can paste the rendered text back) for tone/consistency.
5. **Claude:** Makes any final targeted wording tweaks in code.

**Why:** ChatGPT is more token-efficient for open-ended brainstorming; Claude is needed only for the actual code insertion and live verification.

### Strategy doc rewrite (Sections 5 & 9, tasks 2)
1. **ChatGPT:** Rewrites `MARKET_POSITIONING.md`, `POSITIONING_ARCHITECTURE.md`, `BUSINESS_BLUEPRINT.md` in full.
2. **Jacob:** Approves.
3. **Claude:** Saves the approved text into the actual files in the repo (or Jacob can do this himself since they're just markdown files).

**Why:** No code logic is involved — the only reason to loop Claude in at all is to write the files back into the repo, which is a trivial file-write, not a reason to burn Claude context on drafting.

### Legal/SOW rework
1. **ChatGPT:** Drafts the revised hourly-billing SOW/proposal template.
2. **Jacob:** Reviews, and eventually a real attorney reviews.
3. **Claude:** Only needed if the template should be wired into the website or a document-generation flow later.

---

## 12. Ideal Client Profile

**PROFILE A — Original strategy docs (FACT, but flagged stale vs. new direction):**
- Company size: 10-250 employees, established revenue.
- Operational complexity: recurring document/email/spreadsheet work, visible backlog or service bottleneck.
- Decision maker: owner/operator who can sponsor change; a process owner must be assignable.
- Industries (Wave 1): accounting/bookkeeping operations, commercial real estate/property management, construction/specialty contractors, recruiting/staffing, architecture/engineering admin, established B2B services.
- Buying triggers: new system rollout, growth without proportional hiring, backlog, key-employee departure, M&A integration, margin pressure, service-quality failures, leadership mandate, competitor adoption, major software renewal, audit/security event.
- Disqualifiers: no executive sponsor, no process owner, requests to evade policy/law, expects unsupervised consequential AI decisions, won't provide baseline access, no budget, wants "magic prompts" without process change.
- Sales cycle / project value: **UNKNOWN** (not quantified in the docs).

**PROFILE B — New direction (ASSUMPTION, driven by this session's conversation, not yet formally written up anywhere):**
- Smaller businesses, plausibly solo-to-small-team, referred through a bookkeeper's existing client relationships.
- Geography: Queens/NYC area specifically named.
- Pain point pattern (from the actual case study used on the site): manual, repetitive bookkeeping/data-entry work eating an operator's time; desire to free up capacity to take on more clients rather than to cut headcount.
- Buyer: likely the business owner directly, or the bookkeeper/CPA recommending EchoFrame to their own client.
- Budget/sales cycle/project value: **UNKNOWN.**

**These two profiles have not been reconciled — flagged in Sections 2 and 7 as an open task.**

---

## 13. Customer Problems

| Problem | Who experiences it | Current cost/pain | What EchoFrame would do | Expected outcome | Already part of the offer? |
|---|---|---|---|---|---|
| Manual bookkeeping/data entry (deposit matching, reconciliation) | Bookkeepers, small business owners | Hours of manual, repetitive, error-prone work per week | Build automated matching/reconciliation workflows against existing systems (e.g., QuickBooks API) | Hours freed up; fewer errors; capacity for more clients | Yes — "Bookkeeping & Financial Workflow Automation" |
| Multi-entity/intercompany tracking complexity | Owners running multiple businesses/tax IDs | Manual cross-referencing, risk of blending books | Master tracking view across entities | Clean separation with visibility | Yes — "Multi-Entity & Intercompany Tracking" |
| General repetitive manual processes (spreadsheets, inboxes, disconnected tools) | Any small business | Time cost, inconsistency | Custom process/workflow automation | Reliable automated workflow | Yes — "Process & Workflow Automation" |
| Slow/inconsistent customer communication and lead follow-up | Small businesses with inbound leads | Lost/delayed leads | AI-assisted intake/scheduling/follow-up | Faster, more consistent response | Yes — "Customer Communication & Lead Follow-Up" |
| Lack of a clean, current view of business performance | Owners | Decisions made on stale/incomplete data | Build reporting/owner dashboards from existing systems | Real-time visibility, no new software purchase required | Yes — "Reporting & Owner Dashboards" |
| Staff not equipped to run/extend what's built | Any client with employees | Dependency on the vendor | Hands-on staff training | Team can run and extend the system | Yes — "Staff Training" |
| Unclear access/security posture as the business grows | Growing small businesses | Risk exposure | Systems & security review | Clearer access control | Yes — "Systems & Security Review" |
| Ongoing need for troubleshooting/new automation/staying current on AI | Existing clients post-implementation | Vendor lock-in or stagnation | Month-to-month hourly ongoing consulting | Continuous improvement without a new sales cycle | Yes — "Ongoing AI Consulting" |
| Lack of AI strategy/prioritization (which use case first) | Any prospect | Decision paralysis | "Workflow Discovery & Opportunity Mapping" first visit | A plain-language prioritized list | Yes — entry point of the service list |

---

## 14. Service Inventory

All services below share the same commercial terms: **$40/hour** for actual
hours worked, a **travel fee** quoted per trip for onsite work (~$1,250
typical for a single-day regional trip), and a **$50/day onsite food
stipend**. There is no separate fixed price per service — this is a
deliberate design choice (see Section 4). Source: `website/lib/services.ts`.

1. **Workflow Discovery & Opportunity Mapping** — Category: Get started.
   A focused first visit to map how work actually moves and produce a
   plain-language list of what's worth fixing first. For: any new
   prospect. Status: live on site. Open question: none.
2. **Bookkeeping & Financial Workflow Automation** — Category: Financial
   operations. Deposit matching, bank/card reconciliation, bill intake &
   approval routing, payroll entry prep, built to sit inside QuickBooks or
   whatever the client already uses. For: bookkeepers/small businesses.
   Status: live. This is the closest analog to the real Dr. Hendizadeh
   proposal work.
3. **Multi-Entity & Intercompany Tracking** — Category: Financial
   operations. For owners running more than one business/tax ID. Status:
   live.
4. **Process & Workflow Automation** — Category: Operations. General
   repetitive manual work rebuilt as automation. Status: live.
5. **Customer Communication & Lead Follow-Up** — Category: Operations.
   AI-assisted intake/scheduling/follow-up. Status: live.
6. **Reporting & Owner Dashboards** — Category: Operations. Built from
   existing systems, no new software purchase implied. Status: live.
7. **Staff Training** — Category: Team enablement. Hands-on training so
   the team can run/extend what's built. Status: live.
8. **Systems & Security Review** — Category: Team enablement. Access
   review as the business grows. Status: live.
9. **Ongoing AI Consulting** — Category: Stay current. Month-to-month,
   hourly, troubleshooting + new automations + staying current on new AI
   tools. Status: live. This is the closest thing to a recurring-revenue
   product currently defined.

**Open task (explicitly requested by Jacob, not yet done):** Expand this
into a fuller "catalog containing ideas of services" — see Section 9,
task 7.

---

## 15. Offer Ladder

**Current (live) ladder:**
1. Discovery conversation (free, informal) →
2. Written hourly quote (scoped to the specific problem, includes travel
   fee/stipend if onsite) →
3. Agreement (informal written confirmation, not yet a finalized legal
   template for the hourly model) →
4. Kickoff / hours billed as worked →
5. Invoice for hours + travel + stipend →
6. (Optional) Ongoing AI Consulting retainer, month-to-month, hourly.

**Old (superseded) ladder, for reference:** Fit call → Qualification →
Paid diagnostic (O1, $2,500) → Build sprint (O2) or Transformation (O3) or
Enterprise program (O4) → Assurance/support retainer (O5).

**Gaps:**
- No formal "diagnostic as a distinct paid step" in the new model — the
  discovery conversation is currently framed as free/informal, unlike the
  old O1 diagnostic which was itself a $2,500 paid product. Whether
  Jacob wants a paid diagnostic step reintroduced under the hourly model
  is **UNRESOLVED.**
- No formal proposal/SOW template exists yet for the hourly model (see
  Section 9, task 3).

---

## 16. Pricing

**FINAL / APPROVED (current, live):**
- Hourly rate: **$40/hour**, billed for actual hours worked.
- Travel fee: flat fee quoted per trip to cover mileage/airfare and
  lodging; a typical single-day regional trip runs **~$1,250**; confirmed
  before booking, not a fixed universal number.
- Onsite food stipend: **$50/day** for any day worked onsite at a client
  location.
- No fixed packages, no public checkout, no self-serve payment. Every
  project is quoted individually after a discovery conversation.

**SUPERSEDED (kept in the repo, not deleted, not currently sold):**
- O1 Workflow Opportunity Diagnostic: $2,500 (deposit $2,500), 10 business
  days.
- O2 Workflow Build Sprint: $7,500 (deposit $3,750), 4 weeks.
- O3 AI Operations Transformation: $18,000 (deposit $7,200), 8-10 weeks.
- O4 Enterprise AI Operations Program: $45,000 (deposit $13,500), 16-20
  weeks.
- O5 Workflow Assurance & Enablement: $2,500/month (deposit $2,500),
  3-month initial term.

**CLAUDE RECOMMENDATION (not decided):** Consider whether a paid
diagnostic/discovery step should exist under the hourly model too (i.e.,
bill a small number of hours for the first visit rather than treating
discovery as fully free) — this is how the real Dr. Hendizadeh proposal
actually works (the first visit is itself billed at $40/hr + travel).
**This may already effectively be the intent** — worth explicitly
confirming with Jacob rather than assuming discovery is free.

**Real-world precedent:** The Dr. Hendizadeh proposal (`Plan for Dr.
Hendizadeh.pdf`) is the actual, real pricing structure this was modeled
on: $40/hour + a $1,250 flat travel fee for "Trip 1," with named add-on
modules each carrying their own flat base/setup fee (e.g., Check Intake
$650, Bill Intake $950, Bank/Card Reconciliation $1,100, Payroll Entry
Prep $750, Intercompany Tracking $900, Full Tenant/CRE Workflow $1,500,
Systems & Security Review $600, Staff Training $500) plus $40/hour for
any time beyond the base. **Note:** the live website currently does NOT
include per-service flat base fees like this proposal does — it's purely
hourly across all 9 services. Whether to reintroduce per-service base
fees (matching the real proposal precedent more closely) is
**UNRESOLVED** and worth flagging to ChatGPT/Jacob.

**How ROI/client size should influence pricing:** Not addressed in the new
model. The old model scaled price with client size/complexity (department
count, workflow count, user count) via the tiered packages; the new
hourly model has no explicit mechanism for this beyond "more hours for
more complex work." **Gap worth flagging.**

**Geographic pricing:** Not addressed beyond the travel fee itself scaling
with distance.

---

## 17. Business Model

- **Customer acquisition:** Primarily referral-driven right now, via
  Jacob's aunt's bookkeeping client relationships in Queens/NYC. No other
  lead-generation channel has been confirmed active this session (the old
  `sales/` docs describe a broader outreach/referral system built for the
  old model — unreviewed this session, may still be partially usable).
- **Revenue stages:** Discovery conversation (currently free) → quoted
  hourly project (one-time revenue) → optional Ongoing AI Consulting
  retainer (recurring, hourly, month-to-month).
- **Recurring revenue:** Only the "Ongoing AI Consulting" line is
  recurring, and it's still hourly/usage-based, not a fixed retainer fee
  (unlike the old O5 which was a flat $2,500/month with a 3-month minimum
  term).
- **Expansion/upsell:** Not formally defined under the new model. The old
  model had explicit upsell paths (diagnostic credit toward a build
  sprint, additional 10-hour support blocks, etc.) — none of that has been
  recreated for the hourly model yet.
- **Productized services / software revenue / licensing:** None currently.
  Everything is time-based service revenue.
- **Gaps:** No formalized recurring-retainer product; no explicit
  upsell/expansion path; no lead-gen channel beyond the one referral
  relationship currently identified.

---

## 18. Client Delivery Model

| Stage | Exists today? | Notes |
|---|---|---|
| 1. Lead | Partial | Referral channel identified (aunt); no formal lead capture beyond the website contact form |
| 2. Qualification | Not formalized for new model | Old `sales/` docs have a qualification framework, unreviewed this session |
| 3. Intro/discovery call | Yes (conceptually) | "Discovery conversation" is step 1 of the live `EngagementJourney` component |
| 4. Discovery/data collection | Exists generically | `client-delivery/CLIENT_INTAKE.md`, `DEPARTMENT_INTERVIEW.md`, `BUSINESS_OWNER_EMPLOYEE_QUESTIONNAIRES.md` — built for the old model, likely still adaptable |
| 5. Workflow analysis | Exists generically | `client-delivery/WORKFLOW_INVENTORY.md`, `CURRENT_FUTURE_STATE_MAP.md` |
| 6. AI opportunity assessment | Exists generically | `client-delivery/AI_OPPORTUNITY_REPORT.md`, `OPPORTUNITY_AND_ROI_ASSESSMENT.md`, `READINESS_MATURITY_ASSESSMENT.md` |
| 7. ROI analysis | Exists generically | `client-delivery/EXECUTIVE_ROI_SUMMARY.md`; `finance/ROI_MODEL.xlsx` (unreviewed, likely stale) |
| 8. Proposal | Partial | Real precedent exists (`Plan for Dr. Hendizadeh.pdf`); no generalized hourly-model template yet (see Section 9, task 3) |
| 9. Contract | Not ready | SOW templates are keyed to old O1-O5 codes; need rework |
| 10. Onboarding | Exists generically | `client-delivery/CLIENT_INTAKE.md` |
| 11. Implementation | N/A — this is Claude/Jacob's actual delivery work per engagement, not a template |
| 12. Testing | Exists as a concept | `client-delivery/TEST_ADOPTION_LAUNCH_CHECKLISTS.md`, `WORKFLOW_IMPLEMENTATION_TEMPLATE.md` |
| 13. Client approval | Not formalized for hourly model | — |
| 14. Training | Exists | `training/*.md`, `client-delivery/EMPLOYEE_AI_HANDBOOK.md` |
| 15. Documentation | Exists | `client-delivery/WORKFLOW_SOP.md`, `PROMPT_INSTRUCTION_LIBRARY.md`, `AI_TOOL_GUIDE.md` |
| 16. Launch | Exists as a concept | `client-delivery/90_DAY_ROADMAP.md`, `AI_IMPLEMENTATION_PLAN.md` |
| 17. Monitoring/support | Partial | "Ongoing AI Consulting" service exists; no formal monitoring process documented |
| 18. Renewal/expansion | Not formalized for hourly model | — |

**Summary:** The *delivery methodology* (client-delivery/, training/,
security/ folders) is extensive and was built to be pricing-model-agnostic
— it should mostly transfer to the new hourly model with light editing.
The *commercial* layer (proposal, contract, upsell path) is what's
actually behind and needs rebuilding for the hourly model.

---

## 19. AI Audit / Assessment Product

- **Purpose (as originally designed):** The old O1 "Workflow Opportunity
  Diagnostic" served this role — a paid ($2,500), 10-business-day
  engagement producing a readiness score, ranked opportunity register, one
  current-state map, and a 90-day roadmap.
- **Under the new hourly model:** No distinct, named "audit" product
  currently exists — "Workflow Discovery & Opportunity Mapping" is the
  closest equivalent but is billed hourly, not as a fixed diagnostic
  product, and it's unclear whether it's free or billed (see Section 16
  recommendation).
- **Supporting frameworks that already exist and are reusable:**
  `client-delivery/READINESS_MATURITY_ASSESSMENT.md`,
  `WORKFLOW_INVENTORY.md`, `OPPORTUNITY_AND_ROI_ASSESSMENT.md`,
  `AI_OPPORTUNITY_REPORT.md`, `training/MODEL_SELECTION_FRAMEWORK.md`.
  None of these were reviewed in full this session — their content is
  **UNKNOWN** in detail, but their existence and purpose are confirmed by
  file name and the original package's design intent.
- **What ChatGPT should build:** A decision on whether the discovery step
  is free or paid under the hourly model, and if paid, a lightweight
  "diagnostic" product definition (scope, typical hours, deliverable)
  consistent with $40/hr billing.

---

## 20. Consulting Methodology

- **Named framework that exists:** "The OWNED Method" — **O**bserve,
  **W**eigh, **N**avigate, **E**ngineer, **D**emonstrate and transfer. This
  is live on the website (`/method` page and homepage) under the EchoFrame
  brand already — it survived the rebrand unchanged.
- **Underlying operating loop (from `strategy/BUSINESS_BLUEPRINT.md`):**
  Discover → map → classify data → score opportunities → design →
  prototype → test → train → launch → measure → transfer → improve. This
  is more granular than the public-facing OWNED acronym and functions as
  the internal version of the same idea.
- **Status:** Finalized as public-facing content; not revised this session
  beyond the brand name around it.

---

## 21. Sales System

- **Lead sources today:** Referral (aunt's bookkeeping clients), website
  contact form. No confirmed cold outreach, LinkedIn, or paid channel
  active this session.
- **Existing but unreviewed-this-session assets:** `sales/SALES_PIPELINE.md`,
  `OBJECTION_AND_CLOSE_PLAYBOOK.md`, `OUTREACH_AND_INTRO_SCRIPTS.md`,
  `EMAIL_AND_REFERRAL_LIBRARY.md`, `SALES_CHECKLISTS.md`,
  `NY_MARKET_ENTRY.md`, `DISCOVERY_SCRIPT_AND_QUESTIONNAIRE.md`. These were
  built for the old positioning/pricing and have not been confirmed
  current.
- **CRM:** No CRM vendor selected (`operations/CRM_AND_FOLDER_SPEC.md`
  exists as a spec, vendor still open per `strategy/OPEN_QUESTIONS.md`).
- **What needs creating:** A referral-specific outreach kit for the
  bookkeeper channel (see Section 9, task 6) — this is the one channel
  Jacob has actually named as real and active.

---

## 22. Website

- **Domain:** Not deployed; actual EchoFrame domain string **UNKNOWN** to
  Claude.
- **Platform:** Next.js 16 (App Router, Turbopack), TypeScript, Vitest for
  tests (72 passing).
- **Pages that exist:** Home, Services, Method, Industries, Training,
  Security, About, Contact, Privacy, Terms, Thank-you, plus the 5 old
  package-specific pages (workflow-diagnostic, build-sprint,
  transformation, enterprise, support) which still exist but are no longer
  linked from navigation.
- **Navigation:** `website/lib/nav.ts` — primary nav (Services, Method,
  Industries, Training, Security, About) and footer nav (updated this
  session to point at the new service anchors instead of the 5 old
  package routes).
- **Homepage:** Rewritten this session — hero, "what EchoFrame delivers,"
  case study callout, three-pillar (Consulting/Implementation/Training),
  OWNED Method, services grid, pricing table, closing CTA.
- **Services page:** Rewritten this session to show the 9-item capability
  grid + pricing table instead of the old 5-package comparison table.
- **About page:** Rewritten this session — founder story, Navy
  commissioning disclosure, bookkeeper origin story, address/contact
  (still the Georgia address).
- **Case studies:** None as standalone pages; one case-study-style callout
  embedded in the homepage.
- **FAQ:** Exists (`components/Faq.tsx`), generic content, not reviewed/
  rewritten for the new model this session.
- **Forms:** Contact/lead form exists (`components/LeadForm.tsx`), posts to
  `/api/contact`; no payment form (by design).
- **Integrations:** Stripe (dormant), generic CRM webhook (vendor unset),
  Resend email (planned, not confirmed configured), Upstash Redis
  (optional rate-limit/idempotency store).
- **SEO/Analytics:** Basic metadata present per page; analytics
  integration status **UNKNOWN/not configured this session.**
- **What ChatGPT can work on without touching implementation:** All page
  *copy* (further refinement), FAQ content, About page narrative details,
  meta descriptions/titles — anything that's text Jacob can hand back to
  Claude to paste in.

---

## 23. Brand

- **Business name:** EchoFrame.
- **Logo:** Real asset, a navy open-frame/bracket icon with three
  horizontal "echo" lines (the middle line accented in gold) beside a
  serif "EchoFrame" wordmark, on a transparent background. Source files:
  `EchoFrame/site/echoframe-logo.png` (full lockup) and
  `echoframe-icon.png` (icon only), from Jacob's original EchoFrame
  project. Copied into the website; original files untouched.
- **Colors:** Logo's native colors are navy (~`#14284f`) and gold
  (~`#b8902f`) — added as CSS variables (`--brand-navy`, `--brand-gold`)
  but **not yet applied** to the rest of the site. The site's actual
  current chrome color is a powder-blue/periwinkle (`#7297c5`), inherited
  from the old "White Oak Operations" design system, which Jacob
  explicitly likes and wants kept for now. **Final palette is
  undecided/paused, not finalized.**
- **Fonts:** Serif display font (Georgia/"Iowan Old Style"/Times New Roman
  stack) for headlines, system sans-serif for body/nav — inherited from
  the old design system, unchanged this session.
- **Voice/tone:** Confident, declarative, Title Case headlines,
  "modern corporate" register explicitly modeled on BCG/Bain/Deloitte —
  blended with a personal, named-founder voice (not an anonymous "we").
  Earlier in the process Jacob also asked for "Southern charm" warmth;
  the current copy leans corporate-confident more than folksy-warm, and
  this may need rebalancing (flagged in Section 2).
- **What to avoid:** Casual/"AI blog" phrasing (explicitly called out and
  removed this session); overselling ("guaranteed savings" language is
  avoided throughout, consistent with older guardrail docs); anything
  implying automation replaces bookkeepers/CPAs rather than assisting
  them.
- **Existing brand assets beyond the logo:** The original EchoFrame
  venture also has a navy background brand asset
  (`EchoFrame Navy Background.png`) and other marketing collateral (ads,
  a marketing plan, an intro card/carousel) — these belong to the OLD
  EchoFrame venture and were not pulled into the new site beyond the logo
  itself.
- **Finalized:** Name and logo. **Not finalized:** color palette, final
  tone balance.

---

## 24. Marketing

- **Website:** Live locally, functioning as the main marketing asset once
  deployed.
- **Referral/bookkeeper channel:** The one concrete, real channel
  identified — not yet formalized into a repeatable outreach kit (see
  Section 9, task 6).
- **SEO/content/LinkedIn/social/paid ads/webinars:** **UNKNOWN /
  not discussed this session.** Older `sales/` docs may contain relevant
  material (unreviewed).
- **Case studies:** One informal case study (the bookkeeper story) exists
  as homepage copy; not yet a standalone, detailed case study document.
- **Tasks ChatGPT can take over:** Referral kit copy, case-study writeup,
  any future SEO/content strategy, LinkedIn positioning for Jacob
  personally (relevant given the personal-founder brand voice).

---

## 25. Technology Stack

| Technology | Current use | Planned use | Client- or internal-facing | Required? | Claude's current work with it |
|---|---|---|---|---|---|
| Next.js 16 / TypeScript | Website framework | Same | Internal (build) / client-facing (output) | Yes | Actively edited this session |
| Vitest | Test suite (72 tests) | Same | Internal | Yes | Verified passing after every change |
| Stripe | Dormant (old checkout/webhook code, untouched) | Unclear — no public checkout planned | Internal | No (not currently) | Left untouched by explicit instruction |
| Resend | Planned transactional email (per `.env.example`) | Contact form notifications | Internal | Likely | Not configured/tested this session |
| Upstash Redis | Optional durable store for rate-limit/idempotency | Same | Internal | Optional | Not touched this session |
| Vercel | Hosting target | Deployment | Internal | Yes, for launch | Blocked per prior session notes; not re-attempted |
| IONOS | Domain registrar/DNS (per old docs) | Same, assuming EchoFrame domain sits here too | Internal | Yes, for launch | Not touched this session |
| Generic CRM webhook | Lead routing hook exists in code (`lib/crm.ts`, `lib/lead-routing.ts`) | Vendor still unselected | Internal | Eventually | Not touched this session |
| Claude (Claude Code) | Full repo access, code editing, live browser preview | Continued implementation/deployment work | Internal (Jacob's tool) | — | This session's primary tool |
| ChatGPT | Not yet used for this business | Strategy/copy/research per this handoff | Internal (Jacob's tool) | — | N/A until Jacob starts using it per this doc |

---

## 26. AI Implementation Capabilities

Based on the services actually offered (Section 14) and the real
Hendizadeh proposal, the kinds of AI/automation solutions in scope are:

- **Current/near-term capability (proven, has a real precedent):**
  QuickBooks-API-based deposit matching and record automation (the
  bookkeeper case study and the Hendizadeh proposal's "EFT Deposit
  Matching" and "Five-Entity Control Center" are direct examples).
- **Planned/implied by the service list:** bill intake & approval routing,
  bank/credit-card reconciliation automation, payroll entry prep,
  intercompany transaction tracking, tenant/CRE workflow automation,
  customer communication/lead-follow-up automation, reporting dashboards.
- **Not yet built/experimental:** No mention of custom multi-agent
  systems, RAG systems, or employee "copilots" as a named offering — the
  positioning is deliberately about practical, scoped automation of
  specific workflows rather than general-purpose AI agent products.
- **Explicitly out of scope / gated (from the old strategy docs, likely
  still directionally true):** legal advice generation, clinical
  decisions, PHI workflows, lending/underwriting, investment
  recommendations, employment screening/ranking, biometric surveillance,
  fully autonomous customer commitments, safety-critical control — these
  require counsel/security review before ever being offered.

---

## 27. Security, Privacy, and AI Governance

- **Existing policy set (unreviewed in full this session, but present and
  purpose-built):** `security/AI_ACCEPTABLE_USE_POLICY.md`,
  `PII_PHI_FINANCIAL_GUIDANCE.md`, `CLIENT_DATA_POLICY.md`,
  `DATA_CLASSIFICATION_AND_HANDLING.md`, `APPROVED_TOOL_FRAMEWORK.md`,
  `ACCESS_CREDENTIALS_MFA.md`, `OFFBOARDING_AND_DELETION.md`,
  `SECURITY_REVIEW_CHECKLIST.md`.
- **Stated guardrails (from `strategy/ASSUMPTIONS.md` and the site itself):**
  no sensitive data submitted to AI systems by default; client approval,
  vendor terms, access controls, and a documented data path are
  prerequisites; PHI use is prohibited until counsel/security confirm a
  compliant architecture.
- **The Hendizadeh proposal itself models good practice here:**
  per-person logins with MFA, no shared passwords, no payment without
  sign-off, logged/timestamped automated actions, CPA-confirmed account
  mappings, client retains ownership/admin control, PHI-adjacent data
  (remittance files) handled under appropriate safeguards.
- **What still needs professional review:** Everything — no security/
  governance policy in this repo has been confirmed reviewed by a security
  professional or attorney; they are internal drafts.

---

## 28. Legal / Business Infrastructure

- **Entity formation:** **Not decided.** Explicitly and repeatedly marked
  pending on every public legal page.
- **Business banking, insurance:** **UNKNOWN / not discussed.**
- **Contracts:** MSA, NDA, DPA, ToS, Privacy Policy, cancellation/refund
  policy, and travel expense policy all exist as drafts in `legal/`, all
  marked "attorney review required." SOW templates exist per old offer
  code (O1-O5) and need rework for hourly billing.
- **IP/client ownership:** The general principle stated across delivery
  docs is that clients retain ownership of their own systems/data and
  gain "ownership transfer" of what's built for them — not formalized
  into binding contract language for the hourly model yet.
- **Contractor agreements:** N/A — solo practice currently.
- **Taxes/bookkeeping:** **UNKNOWN** — flagged in the old `OPEN_QUESTIONS.md`
  as needing CPA validation; not addressed this session.
- **Open tasks:** Entity formation decision; counsel selection (the old
  docs explicitly warn not to assume New York governing law just because
  early clients are there — counsel choice should weigh entity formation
  state, principal place of business, where services are performed, and
  client location); rewrite SOW templates for hourly billing.

---

## 29. Real Client or Prospect Examples

### Dr. Pedy Hendizadeh — Financial Workflow Consulting Proposal
- **Type of company:** Five podiatry practices under five separate tax
  IDs, plus a commercial real estate portfolio (~50 tenants).
- **Problem:** No unified visibility across five legally separate entities;
  incoming payments (mostly EFT, some check) not systematically matched/
  reconciled.
- **Proposed solution ("Trip 1"):** A "Five-Entity Control Center" (master
  record linking each tax ID to its practices/properties/accounts), EFT
  deposit matching with an exception list for anything unclear, and one
  polished owner-level summary report — billed at $40/hour plus a $1,250
  flat travel fee for the visit.
- **Ongoing relationship offered:** Month-to-month hourly availability
  after Trip 1 for troubleshooting, building add-on modules, and
  eventually training staff; optional guaranteed monthly availability.
- **Add-on modules offered (each a flat base fee + $40/hr beyond):** Check
  Intake & Deposit Register ($650), Bill Intake/Duplicate Detection/
  Approval Routing ($950), Bank & Credit Card Reconciliation ($1,100),
  Payroll Entry Prep ($750), Intercompany Transaction Tracking ($900),
  Full Tenant & CRE Workflow ($1,500), Systems & Security Review ($600),
  Staff Training ($500).
- **Why this is relevant:** This proposal is the actual real-world
  precedent for the entire pricing pivot this session — it's the direct
  source of the $40/hr rate and the travel-fee concept, and its per-module
  base-fee structure is a live open question for whether the general
  website should adopt the same pattern (see Section 16).
- **Lessons learned:** Real engagements are individually scoped with
  named, concrete deliverables and controls (MFA, no shared passwords,
  CPA-confirmed account treatment, PHI-adjacent data handled carefully) —
  this is a strong template for future proposals.

### The bookkeeper case study (used on the live homepage)
- **Type of company:** A bookkeeper at a 15-location retail business.
- **Problem:** Tracking everything by hand in QuickBooks and Excel.
- **Solution:** An AI workflow using QuickBooks' own API to update records
  automatically, cutting roughly five hours of manual work per day; the
  bookkeeper was also trained to extend the automation herself.
- **Relevance to positioning:** This is the direct model for "assist, don't
  replace" positioning, and closely mirrors (though is not explicitly
  confirmed to be identical to) the story Jacob described about
  automating his aunt's bookkeeping work to free her up for more clients.
  **Whether this is literally the same event or a similar/composite
  example is UNKNOWN** — worth confirming before treating it as a direct
  quote-worthy case study.

---

## 30. Competitive Landscape

**What exists (from `strategy/COMPETITIVE_ALTERNATIVES_AND_OBJECTIONS.md`,
written for the old positioning but generically still relevant):**

- **Alternatives clients consider instead of hiring EchoFrame:** doing
  nothing; asking employees to experiment with AI themselves; buying a
  point-solution SaaS tool; hiring an automation freelancer; using an
  incumbent IT/MSP; engaging a large consultancy; hiring an internal
  AI/ops lead.
- **Objection-response framework:** acknowledge → diagnose the underlying
  risk → provide evidence/boundary → propose the smallest safe next step.
- **Common objections and prepared responses:**
  - *"We can do this ourselves"* → agree, position the engagement as
    acceleration + governance, with skills transfer as the actual goal.
  - *"AI makes mistakes"* → show test evidence, human approval steps,
    restricted actions, logging, fallback paths.
  - *"Our data is sensitive"* → start with data classification and
    low-risk data only; no tool use until controls are approved.
  - *"No time"* → start with one bottleneck, require a named owner.
  - *"Too expensive"* → compare to verified cost/capacity/delay/risk;
    reduce scope, not price integrity.
  - *"Which AI model is best?"* → select per task using tests, not brand
    allegiance.
- **No specific named competitors have been researched this session** —
  this is a good, clean ChatGPT task (Section 9, task 9): actual
  competitive research into small-business AI/automation consultants
  serving the Northeast/NYC bookkeeping-adjacent market specifically.

*(Note: Jacob's original prompt appears to have been cut off mid-sentence
at the start of this section — if there were additional numbered sections
intended beyond 30, they were not received. This handoff covers sections
1 through 30 as specified.)*

---

## Final Notes for ChatGPT

- Treat everything marked **FINAL** in Section 4 as settled — don't
  re-litigate it.
- Treat Section 2's **UNRESOLVED** items and the ICP tension (Section 12)
  as the highest-value open questions to help Jacob actually close out.
- The single most concrete, real thing to build on right now is the
  bookkeeper/aunt referral channel (Queens/NYC) and the Hendizadeh-style
  proposal format — everything else is comparatively abstract.
- Do not pull in anything from Magnolia Grove Consultants. It was never
  referenced in this project and should stay that way unless Jacob
  explicitly says otherwise.
- Do not touch, reference, or reintroduce content from Jacob's prior
  EchoFrame product venture (RateWatch, AutoLedger, CallRouter,
  QuoteRevive, ShiftLens, etc.) unless Jacob explicitly asks for it — only
  the brand name and logo were reused.
