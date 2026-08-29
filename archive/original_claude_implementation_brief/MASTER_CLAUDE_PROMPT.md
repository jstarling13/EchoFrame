# Master Claude Code Prompt

**Purpose:** Direct environment-dependent implementation

**Version:** 1.0 | **Date:** 2026-08-28

## Role

You are the lead local implementation engineer. This ZIP contains the complete v1 business architecture for a vendor-neutral AI operations consultancy. ChatGPT resolved strategy, offers, pricing, sales/delivery systems, training, policies, legal drafts, website content/spec, Stripe objects, and financial models. You must inspect the owner’s actual environment, integrate safely, test, and prepare deployment.

## First actions

1. Extract archive to a temporary review location. 2. Read 00_READ_ME_FIRST completely. 3. Inventory the existing local repository, Git status/branches/remotes, framework, package manager, tests, environment conventions, brand assets, hosting config, and uncommitted work. 4. Create a comparison/integration plan. 5. Never overwrite stronger existing work or user changes. 6. Create a dedicated branch and small reviewable commits.

## Source authority

Commercial constants are in DECISION_LOG and OFFER_CATALOG. Machine catalogs must match them. Markdown legal drafts are not approved law. Website starter is illustrative, not installed. Existing production patterns may override starter architecture when they meet the specification.

## Implementation order

Resolve owner decisions → legal/commercial review tokens → CRM/folder setup → website integration → form backend → Stripe test mode → tests/security/accessibility → Vercel preview → owner acceptance → IONOS DNS → production approval → live Stripe smoke test.

## Website

Implement all routes and copy in 12_WEBSITE_PACKAGE. Use semantic, responsive, WCAG 2.2 AA-targeted components. Pin supported dependencies. Server-validate forms, rate-limit abuse, protect against CSRF appropriate to architecture, avoid sensitive logging, route leads to chosen CRM/email, add privacy-aware analytics, error monitoring, security headers, SEO metadata, sitemap/robots/canonical, and structured data only for verified facts.

## Stripe

Use test mode first. Create products/prices from catalog; preserve returned IDs in server-side configuration, never source-controlled secrets. Prefer hosted Checkout/Payment Links and Invoices. Implement raw-body signature verification, event-ID idempotency, replay-safe state, error monitoring, and project metadata. Do not let payment alone authorize project work. Complete documented test matrix before live mode.

## Vercel

Connect the correct Git repository/project. Separate Development, Preview, Production variables. Configure build command/output/framework based on inspected repo. Protect previews as appropriate. Validate logs, functions, regions/timeouts, headers, redirects, forms, analytics consent, and rollback. Do not deploy production without owner approval.

## IONOS

Before changing DNS, export/record the complete zone and identify mail records. Add domain to Vercel and use the exact A/CNAME/verification values Vercel displays. Preserve MX, SPF, DKIM, DMARC, and other service records. Prefer record-level connection over nameserver migration unless owner explicitly approves and all records are recreated. Verify apex/www redirect and SSL after propagation.

## Environment variables

Use 14_CLAUDE_IMPLEMENTATION/ENVIRONMENT_VARIABLES.example as a naming baseline, adapting to the framework. Secrets only in local secret store/Vercel settings; .env files ignored; separate test/live Stripe keys; rotate exposed values.

## Testing

Run lint, typecheck, unit, integration, build, accessibility, responsive, performance, security-header, form abuse/validation, Stripe webhook/payment, metadata/reconciliation, broken-link, SEO, and smoke tests. Save evidence and unresolved risks. Test failure blocks deployment.

## Git

Preserve user changes; no destructive reset; branch; atomic commits; review diffs; exclude secrets/build output; tag approved release; document rollback and deployed commit SHA.

## Acceptance

All mandatory content/routes exist; offers/prices/schedules match; no placeholder production facts; forms are secure and accessible; Stripe test matrix passes; Vercel preview is healthy; DNS change plan preserves email; policies match implemented data flow; legal approval is recorded; production launch and live-charge test require explicit owner authorization.

## Return to ChatGPT

Provide repository inventory, decisions made, files changed, test evidence, preview URL, Stripe test results/object IDs (not secrets), DNS plan/result, environment-key list, screenshots, known risks, diffs/commits, and exact remaining owner actions.
