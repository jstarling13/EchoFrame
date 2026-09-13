# EchoFrame Custom Domain Connection Runbook

## Open Question
Before doing anything:
**What exact domain should become the canonical EchoFrame domain?**

Possible states:
A. Jacob already owns an EchoFrame domain.  
B. Jacob owns a domain but it is attached to the prior EchoFrame venture.  
C. Jacob does not yet own the desired domain.  
D. The current Vercel URL will remain temporarily.

Claude should determine which state is true.

# Path A — Domain Already Owned

## 1. Inventory Before Changes
Record:
- registrar
- DNS provider
- nameservers
- current A/AAAA/CNAME records
- MX records
- TXT records
- SPF
- DKIM
- DMARC
- any verification records
- current website targets
- current email provider

Take a snapshot/export before editing.

## 2. Add Domain in Vercel
In the `echo-frame` project:
- open Project Settings
- open Domains
- add the desired apex domain
- add the preferred `www` variant if desired
- assign to Production

## 3. Follow Vercel's Exact Current DNS Instructions
Vercel will show the required configuration for the domain.

Use the values displayed in the project UI at implementation time.

Do NOT rely on old tutorials or hard-coded DNS targets.

## 4. Decide Canonical Host
Choose either the apex or `www` as canonical, then redirect the other to it.

Keep this consistent with:
- metadataBase
- canonical URLs
- sitemap
- Open Graph URLs
- Search Console property

## 5. Protect Email
If email already uses the domain, do not delete MX, SPF, DKIM, DMARC, or provider verification records.

Website DNS and email DNS can coexist.

## 6. Verify
Confirm in Vercel:
- domain status valid
- SSL certificate active
- apex resolves
- www resolves/redirects
- production branch serves the site
- no redirect loops

## 7. Update Application Configuration
After the canonical domain is known:
- metadataBase
- canonical URLs
- sitemap hostname
- robots sitemap reference
- Open Graph URLs
- contact-form allowed origins if relevant
- environment variables tied to origin
- webhook callback URLs if relevant

# Path B — Domain Not Yet Owned

## 1. Name Check
Before purchasing:
- entity-name availability
- domain availability
- obvious trademark conflicts
- social handle needs if relevant

## 2. Purchase
Use a reputable registrar or Vercel Domains.

## 3. Security
Enable:
- registrar MFA
- domain lock
- recovery methods
- auto-renew
- accurate ownership/contact records

## 4. Connect to Vercel
Then follow Path A.

# Path C — Existing Domain Belongs to Prior EchoFrame Venture

Do not repoint it until Jacob explicitly decides:
- whether old venture URLs/email must remain available
- whether redirects are needed
- whether old brand materials depend on subdomains
- whether the consulting practice should instead use a new subdomain/domain

No destructive cutover without that decision.

# Completion Record
Record:
- canonical domain
- registrar
- DNS provider
- Vercel project
- date connected
- redirect policy
- email provider
- DNS backup location
