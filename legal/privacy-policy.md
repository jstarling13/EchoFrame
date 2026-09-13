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

## Service providers (verified against live Vercel project env vars, 2026-09-13)
- Vercel — hosting/infrastructure. The only third party currently involved.
- Checked the `echoframe-live` Vercel project's Environment Variables directly: **none are set.** `EMAIL_PROVIDER_API_KEY`/`EMAIL_FROM`/`LEAD_NOTIFICATION_EMAIL` (Resend), `RATE_LIMIT_STORE_URL`/`RATE_LIMIT_STORE_TOKEN` (Upstash), and `CRM_WEBHOOK_URL` are all unconfigured, so none of those integrations are actually active in production today — the live page states this definitively rather than hedging with "if configured."
- Operational consequence, not just a wording issue: with no email/CRM configured, contact-form submissions currently have **no notification path to Jacob's inbox** — leads are only visible in Vercel function logs. Worth fixing operationally, separate from this document.
- Update this list and the live page together before wiring up any of the above.

## AI use
No automated AI system processes or routes contact-form submissions. EchoFrame does not paste submitted name/email/company/inquiry details into general-purpose AI tools (Claude, ChatGPT); Jacob may use those tools separately for generic drafting help that excludes a specific submission's details. If that changes (submitted data starts going into prompts, or an AI system starts auto-processing/routing inquiries), that tool must be named as a service provider above and this section updated before the change ships. AI use during an actual client engagement is addressed in that engagement's SOW, not here.

## Cookies / tracking
None in use today — no GA, Meta Pixel, LinkedIn Insight Tag, Calendly, reCAPTCHA, or similar. No cross-site behavioral tracking, so Do Not Track signals don't change Site behavior; no third party is permitted to collect PII across sites via the Site for behavioral-ad purposes; nothing for a Global Privacy Control signal to opt out of given no sale/share of data. Update this section and the live page together before adding any tracking.

## Sharing, sale, advertising
No sale of personal information. No sharing for third parties' independent marketing. No targeted/cross-context behavioral advertising. Disclosure only if legally required or to protect EchoFrame/clients/others.

## Retention
Contact submissions: ordinarily up to 24 months; may be retained longer where reasonably necessary for legal obligations, security, fraud prevention, dispute resolution, or establishing/defending legal claims (not an unconditional delete-on-request promise — avoids handcuffing EchoFrame against a bad-faith deletion request during e.g. a dispute). Security/technical logs: shorter, per hosting-provider defaults. Engagement records: per the signed agreement, not this policy.

## Privacy rights
Access, correction, deletion, marketing opt-out — contact EchoFrame using the info below. Identity verification may be requested. Response time: within the period required by applicable law (e.g., CCPA uses 45 days + a possible 45-day extension) rather than a voluntary, stricter self-imposed deadline.

## Security
Reasonable safeguards "designed to protect" (HTTPS, access controls) — no absolute-security claim.

## Children's privacy
Directed to business owners/professionals, not children. No knowing collection from anyone under 18.

## Changes
Material changes reflected by updating the effective date.

## Contact
Jacob Starling / EchoFrame, Columbus, Georgia area, (706) 366-1096, jacob.starling@echoframe.net. Residential address removed from all public pages (footer, About, Privacy, Terms) — publish a business mailing address here once one exists.

## Open items for counsel (do not treat as resolved)
- Confirm whether GDPR, CCPA/CPRA, GLBA/Reg S-P, CalOPPA, or other specific statutes actually apply given real traffic/client geography — not assumed here. Note CalOPPA's reach is broader/lower-threshold than CCPA; don't conflate the two.
- Confirm entity structure (Georgia DBA filing vs. LLC) before this graduates from "Jacob Starling d/b/a EchoFrame" to an LLC name, and update this document and the live page together when that happens. A DBA alone does not create a separate entity or provide liability protection.
- Confirm final retention carve-out language and rights-response timeline against counsel's recommendation.
- Re-verify the service-provider list against actual configured environment variables before every material change to vendors.
- If Resend/Upstash/a CRM are ever turned on, update this section and the live page in the same change that flips the config on — not after.
