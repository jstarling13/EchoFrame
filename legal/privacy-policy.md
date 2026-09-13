# EchoFrame Privacy Policy — Business Draft for Attorney Review

**THIS IS A BUSINESS DRAFT, NOT LEGAL ADVICE. QUALIFIED COUNSEL SHOULD REVIEW BEFORE RELYING ON IT AS A FINAL LEGAL DOCUMENT.** It is, however, kept in sync with what actually runs on the live site at `website/app/privacy/page.tsx` — no placeholder instructions, no internal file references, no unresolved template language.

**Effective date:** September 13, 2026

## Business identity
Jacob Starling, doing business as EchoFrame ("EchoFrame," "we," "us"). No LLC or corporation has been formed as of the effective date above. Registered agent, formation state, and governing-law provisions belong in the entity's Terms of Service / formation documents, not this policy.

## Scope: this Site, not client engagements
Covers only echoframe.net (the "Site"). Client-engagement data (financial records, employee information, credentials, API data, internal business documents) is governed by the signed MSA/SOW/DPA for that engagement, not this policy.

## Information collected
Contact-form fields: name, work email, company, role, company website (optional), employee range, state/region, workflow description, urgency, referral source (optional), consent. Plus standard technical/server logs (IP, browser, device) for security/abuse prevention. No payment info, financial account numbers, health information, or government IDs are collected through the Site.

## How it's used
Respond to inquiries, evaluate fit, keep a record; log data used to operate/secure/troubleshoot the Site.

## Service providers (verified against the actual codebase)
- Vercel — hosting/infrastructure.
- Resend — transactional email, if `EMAIL_PROVIDER_API_KEY`/`EMAIL_FROM`/`LEAD_NOTIFICATION_EMAIL` are configured (`website/app/api/contact/route.ts`).
- Upstash — rate-limiting store, if `RATE_LIMIT_STORE_URL`/`RATE_LIMIT_STORE_TOKEN` are configured (`website/lib/rate-limit.ts`).
- No CRM, marketing platform, or ad network is currently wired up (`CRM_WEBHOOK_URL` is unset by default — see `website/lib/crm.ts`). Update this list and the live page together before adding one.

## AI use
No automated AI system processes or routes contact-form submissions. Jacob may use general-purpose AI assistants (Claude, ChatGPT) as a personal drafting aid when responding to inquiries. AI use during an actual engagement is addressed in that engagement's SOW, not here.

## Cookies / tracking
None in use today — no GA, Meta Pixel, LinkedIn Insight Tag, Calendly, reCAPTCHA, or similar. Update this section and the live page together before adding any.

## Sharing, sale, advertising
No sale of personal information. No sharing for third parties' independent marketing. No targeted/cross-context behavioral advertising. Disclosure only if legally required or to protect EchoFrame/clients/others.

## Retention
Contact submissions: up to 24 months or until deletion is requested, whichever is first. Security/technical logs: shorter, per hosting-provider defaults. Engagement records: per the signed agreement, not this policy.

## Privacy rights
Access, correction, deletion, marketing opt-out — contact EchoFrame using the info below. Identity verification may be requested. Target response time: within 30 days.

## Security
Reasonable safeguards "designed to protect" (HTTPS, access controls) — no absolute-security claim.

## Children's privacy
Directed to business owners/professionals, not children. No knowing collection from anyone under 18.

## Changes
Material changes reflected by updating the effective date.

## Contact
Jacob Starling / EchoFrame, 17 Ridgeway Drive, Cataula, GA 31804, (706) 366-1096, jacob.starling@echoframe.net.

## Open items for counsel (do not treat as resolved)
- Confirm whether GDPR, CCPA/CPRA, GLBA/Reg S-P, or other specific statutes actually apply given real traffic/client geography — not assumed here.
- Confirm entity structure before this graduates from "Jacob Starling d/b/a EchoFrame" to an LLC name, and update this document and the live page together when that happens.
- Confirm final retention period and rights-response timeline against counsel's recommendation.
- Re-verify the service-provider list against actual configured environment variables before every material change to vendors.
