# Founder Credential Setup Runbook

Prepared 2026-08-30. Instructions only: no accounts, keys, products, DNS records, or deployments were created by this package.

## Start here

EchoFrame is the selected working name, pending trademark, entity-name, domain, and common-law clearance. The business operates from Georgia and initially serves New York clients. Do not enter the working name as an already-formed legal entity or invent registration facts in a provider's onboarding form. Use verified legal information; stop where an unresolved entity decision prevents accurate registration.

These are real third-party accounts. For this founder-controlled runbook, **you personally create or sign into each account, accept its terms, complete verification, approve any charges, and obtain its credentials**. ChatGPT cannot invent or generate valid real API keys in a document. Actual keys are issued by providers. Some providers allow authenticated APIs or authorized AI integrations to request keys, so it would be inaccurate to claim that automation can never do so; no such authorization or provisioning is part of this package. Stripe test transactions are simulated, but the account and its credentials are real. Resend and Upstash can incur real usage charges even during Preview testing.

Use a password manager, MFA/passkeys where available, and separate Preview/test credentials from future Production credentials. Never paste secrets into chat, a screenshot, a committed file, source code, a terminal command saved in history, or a public client-side environment variable. Claude may inspect variable **names, presence and validation outcomes**, not print their values. No Homebrew, GitHub CLI or Stripe CLI installation is required for the dashboard steps below.

## 0. One read-only check for Claude

Before you enter values, ask Claude to inspect `/Users/jacob/AI-Consulting-Business/website` and the existing handoff without overwriting either. It should confirm:

- Actual environment-variable references in the application, Stripe sync script and validation guards.
- Current Git branch, clean/dirty status, remote, Vercel project and account permissions; previous reports of missing access are not current proof.
- How the sync script securely loads local environment values; a `.env.local` file is not automatically loaded by every standalone TypeScript runner.
- The exact Stripe Price ID names consumed by the code and whether restricted test keys are accepted by its environment guard.

The supplied `env-template.txt` defines a **proposed canonical mapping**, not an independently audited map of your current repository. Its `STRIPE_PRICE_O2`–`STRIPE_PRICE_O4` and `STRIPE_PRICE_O5_MONTHLY` names must be reconciled with any existing `_DEPOSIT` or `_MONTHLY` names before use. Claude should report a name-only mapping and update the template to match confirmed code, not silently change payment behavior. Do not add nonexistent settings simply because a template lists them.

## A. Stripe account and test-mode keys

1. Open the [Stripe Dashboard](https://dashboard.stripe.com/) yourself. Create an account or sign into the business-owned account you intend to use. Complete email verification and security setup; provide only accurate identity/business information.
2. Select the intended account and its test environment or sandbox. Confirm the interface indicates testing, not live payments. All test products, prices, API keys and webhook destinations below must belong to that same environment.
3. Open **Developers/Workbench → API keys**, using Dashboard search if labels differ. Prefer a restricted **test** API key with the permissions needed by the application. Have Claude identify required API operations without seeing the key. A product-creation script needs broader permissions than runtime payment handling; use a separate temporary setup key if appropriate, then revoke it after sync.
4. Store the runtime test key in your password manager. It will populate `STRIPE_SECRET_KEY`, even if the actual value is a restricted key. Restricted test keys have an `rk_test_` prefix; ordinary test secret keys have an `sk_test_` prefix. A publishable test key has a `pk_test_` prefix and is not interchangeable with either. Never use live keys for Preview. If existing code rejects restricted test keys, Claude must review and test a narrowly scoped correction that continues rejecting all live keys outside Production; do not bypass the environment guard.
5. A publishable key is not required by the reported server-redirect-only Checkout flow. Obtain one only if actual client-side Stripe code requires it; do not add a frontend integration for this task. API keys are explained in [Stripe's key documentation](https://docs.stripe.com/keys), with least-privilege setup in [restricted API keys](https://docs.stripe.com/keys/restricted-api-keys).
6. With secure local loading verified, authorize Claude to run the repository's existing `npm run stripe:sync` in **test mode only**. You enter the key locally yourself without exposing it to chat or shell history. If no working sync script exists, stop and have Claude report the missing implementation rather than invent commands. Do not upgrade the SDK/API version just to run this setup.
7. Review the resulting test products and prices in Stripe. Record Price IDs in your password manager/configuration record and map them to the actual code names. Initial private payment amounts must match this table; later milestones are separately invoiced, not charged as part of the initial deposit:

| Offer | Contract value | Initial private payment/price | Subsequent service payments |
| --- | --- | --- | --- |
| O1 Workflow Opportunity Diagnostic | $2,500 | $2,500 one-time | None |
| O2 Workflow Build Sprint | $7,500 | $3,750 one-time | $3,750 |
| O3 AI Operations Transformation | $18,000 | $7,200 one-time | $5,400; $5,400 |
| O4 Enterprise AI Operations Program | $45,000 | $13,500 one-time | $11,250; $11,250; $9,000 |
| O5 Workflow Assurance & Enablement | $2,500/month; 3-month minimum | $2,500 recurring monthly | $2,500 monthly; $7,500 across initial term |

8. Webhook setup comes after a reachable Preview endpoint exists in section D. Its signing secret is distinct from an API key and belongs to that exact endpoint/test environment. Do not copy a local CLI forwarding secret into the deployed endpoint's configuration. Signature handling is covered in [Stripe webhooks](https://docs.stripe.com/webhooks).

**Done when:** the correct test account is identified, a runtime test key is safely stored, and test Price IDs match the table. No live payments or public payment buttons are enabled. The contractual three-month minimum is not enforced merely by creating a recurring Stripe Price.

## B. Resend account, key and sender verification

1. Open [Resend](https://resend.com/), create/sign into your business-controlled account, verify your email and enable available account security protections.
2. Open **API Keys → Create API Key**. Name it for EchoFrame Preview, select sending-only permission, and restrict it to the intended domain when available. Store the displayed key securely; this supplies `EMAIL_PROVIDER_API_KEY`. See [Resend's API-key instructions](https://resend.com/docs/create-an-api-key).
3. If you already control an approved domain/subdomain, open **Domains → Add Domain**, enter that domain, and follow the displayed DNS verification instructions. Copy the exact names, types and values Resend supplies into that domain's authoritative DNS host. Verify the status becomes successful before using a sender there. Do not assume IONOS is the authoritative host merely because it is the registrar. See [verified domains](https://resend.com/docs/dashboard/domains/introduction).
4. If no domain is chosen or controlled, do not fabricate one or change DNS. For restricted internal testing, use the test sender offered by the Resend dashboard and set `LEAD_NOTIFICATION_EMAIL` to your Resend account email. Resend's shared test domain only permits ordinary recipient delivery to the account-associated address; it is not ready for real client correspondence. See [test-domain restrictions](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain).
5. `EMAIL_FROM` is the exact approved sender address, optionally with an approved display name if the code supports it. `LEAD_NOTIFICATION_EMAIL` is the real inbox you personally monitor. These are configuration values, not automatically your public support/privacy addresses; those business facts remain unresolved in the legal drafts.
6. Send a synthetic test inquiry after Preview deployment. Check both the actual inbox and Resend delivery status, then confirm a failure does not misleadingly tell the user the inquiry was delivered. Do not send real client records in this test.

**Done when:** the API key is safely stored and either a verified-domain sender works or the restricted test-only limitation is documented. A domain-free test is not approval for public launch.

## C. Upstash Redis and REST credentials

1. Open the [Upstash Console](https://console.upstash.com/) and personally create/sign into your account. Review plan limits, region, expected usage and possible charges before confirming a database.
2. Create a separate Redis database for Preview. Choose its region after checking the app's deployment region and any data-location constraints; no region is assumed in this package. Do not use a Production database for test payment events.
3. Open the database details/connection area and find the **REST URL** and **REST token**. Copy them directly into your password manager. The REST URL is an HTTPS endpoint, not the Redis TCP connection string.
4. Map the provider's `UPSTASH_REDIS_REST_URL` value to the app's `RATE_LIMIT_STORE_URL`; map `UPSTASH_REDIS_REST_TOKEN` to `RATE_LIMIT_STORE_TOKEN`, if those application names are confirmed in step 0. Use a token capable of the required reads and writes, not the read-only token: rate limiting and webhook idempotency must change state. See [Upstash connection credentials](https://upstash.com/docs/redis/howto/connect-with-upstash-redis) and [REST access](https://upstash.com/docs/redis/features/restapi).
5. Ask Claude to test read/write/expiry and concurrent duplicate webhook behavior using synthetic records. Do not flush the database. Distinct key namespaces and suitable expirations are required for rate limits versus payment event records. Missing or unavailable durable storage must not silently become an in-memory payment ledger in deployed operation.

**Done when:** both credentials are securely stored and durable behavior is verified in the deployed test environment. Account creation and safe local testing can occur before a Vercel project exists.

## D. Vercel Preview environment variables and verification

1. Sign into [Vercel](https://vercel.com/) yourself. Confirm you are in the intended team and can access the correct project. If no project exists, an authorized owner must create/import it, with **Root Directory = `website`**. A 403 permission failure is a stop condition, not a reason to retry around access controls. Importing a Git repository does not itself override team permissions. Do not approve a Production deployment as a side effect of import; have Claude establish a Preview-only path before the first deploy.
2. Open the project's **Settings → Environment Variables**. For each confirmed name, paste its real value from your password manager, select **Preview only**, and, if appropriate, scope it to `website-implementation`. Do not select Production. Mark server secrets sensitive where supported. See [Vercel environment variables](https://vercel.com/docs/environment-variables).
3. Add the Stripe test runtime key and confirmed test Price IDs, Resend key/sender/recipient, and Upstash REST URL/token. `NEXT_PUBLIC_SITE_URL` must be the actual approved Preview origin with HTTPS and no path. Ask Claude to establish a stable branch Preview URL or explicitly approved test alias; never invent a domain. CRM is optional under the reported email-first implementation: leave CRM variables absent unless a real CRM endpoint and signing arrangement exist.
4. Leave `STRIPE_WEBHOOK_SECRET` unset until the actual test endpoint is created. The initial deploy may expose the webhook route in a deliberately unconfigured/fail-closed state; it is **not payment-ready**. If the application refuses to build without a signing secret, Claude must report and resolve the bootstrap sequencing without fake secret values or disabling signature validation.
5. Deploy the implementation branch to Preview, keeping `main` unmerged and Production untouched. Environment changes affect new deployments, so redeploy after changes. Vercel supplies `VERCEL_ENV`; do not set it manually to spoof Production. [System variable documentation](https://vercel.com/docs/environment-variables/system-environment-variables).
6. In Stripe's same test environment, create a webhook event destination for the actual HTTPS Preview origin plus `/api/stripe/webhook`, after Claude confirms the route. Subscribe only to events the inspected handler needs for checkout/payment outcomes, invoices/subscriptions, refunds and disputes. Save the endpoint's signing secret as `STRIPE_WEBHOOK_SECRET` in Preview and redeploy again. Match the webhook API version to the tested handler; do not assume newest is compatible.
7. Check Preview deployment protection. Stripe cannot complete an interactive login. Claude must identify a supported, explicitly approved way for Stripe to reach this endpoint while preserving required access protection and signature verification; do not disable all protection or leak a bypass secret. `noindex` prevents neither access nor data disclosure.
8. Run synthetic tests: genuine lead delivery; failed delivery; invalid form; rate limiting; correct initial charge for every offer; successful/failed and additional-authentication payments; invalid signatures; duplicate and concurrent event retries; refunds; subscription creation, renewal failure and cancellation; durable-store outage. Verify state changes occur once and payment events do not auto-start delivery. Do not introduce a public checkout button to test the private flow.
9. Claude should report pass/fail evidence, URLs safe to share, branch/commit, and configured variable **names only**. Do not include raw form content, credentials or full environment dumps. Leave legal pages draft/noindex and Preview non-indexable. Production requires separate owner approval after legal, security and payment gates are met.

**Done when:** actual deployed Preview tests pass. A successful build or the mere presence of environment variables is not proof of working integrations.

## E. IONOS access needed later

After an approved domain is chosen, you need an IONOS account with permission to manage that domain's DNS, plus its MFA method and access to the domain's existing mail configuration. Domain purchase is not trademark/entity/common-law clearance. No IONOS credential is needed inside the website's `.env` file for manual DNS management.

Before edits, export or record the current zone and identify the authoritative nameservers, website records, MX, SPF, DKIM, DMARC and verification records. Open **Domains & SSL → the selected domain → DNS**; current guidance is in [IONOS DNS management](https://www.ionos.com/help/domains/general-information-about-dns-settings/managing-dns-settings-in-control-center/).

For a verified sender, add only Resend's exact displayed records, checking host/subdomain conventions and avoiding duplicate/conflicting SPF policies. Do not remove existing mail records or replace apex MX with an unrelated sending-subdomain record. Sender verification may require this DNS work earlier than website launch if you elect to use the chosen domain for Preview email.

For a later approved website launch, copy only the exact A/CNAME/verification values shown by the actual Vercel project. Do not use remembered IP addresses or migrate nameservers without separate authorization. Verify apex/www, HTTPS, email delivery and rollback records. The automatic Vercel Preview URL does not require an IONOS website DNS change.

## Final safety checklist

- No live Stripe keys, real card numbers or live charges used for Preview testing.
- No keys entered in chat, client bundles, repositories, screenshots or logs.
- Secrets scoped to Preview; least-privilege access and actual bills reviewed.
- Shared or exposed key: revoke/rotate at its provider, replace the Preview value, redeploy, and review relevant activity; deleting a chat or commit is insufficient. See [Stripe key-management guidance](https://docs.stripe.com/keys-best-practices).
- No public self-serve checkout. Signed agreements and private payment precede kickoff.
- Legal placeholders remain unresolved until verified and approved, not filled with guesses by Claude.
- This package contains 14 files: 12 legal drafts (including five SOWs), this runbook, and the blank environment template. It does not authorize production deployment, DNS edits, paid plan purchases or account creation by an AI agent.
