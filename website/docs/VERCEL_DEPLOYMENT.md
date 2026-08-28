# Vercel deployment

**Status:** not yet connected. No Vercel project has been created or
deployed by this implementation session — connecting an account/team and
deploying requires the owner's explicit go-ahead (see
`strategy/IMPLEMENTATION_ORDER.md` Phase 5, and
`14_CLAUDE_IMPLEMENTATION/MASTER_CLAUDE_PROMPT.md`: "Do not deploy
production without owner approval").

## What's ready

- `npm run build` succeeds cleanly (Next.js 16, Turbopack) — see
  `IMPLEMENTATION_REPORT.md` for the full command/result log.
- Framework auto-detects as Next.js; no custom `vercel.json` is required.
  Build command: `next build`. Output: managed by the Next.js framework
  preset. Install command: `npm install`.
- Security headers and CSP are set in `next.config.ts` (`headers()`), so
  they apply automatically on Vercel without extra platform config.
- `app/sitemap.ts` / `app/robots.ts` read `NEXT_PUBLIC_SITE_URL` — set this
  Environment Variable in Vercel before the first deploy, scoped per
  environment (see below).

## Steps to connect (owner or Claude, with explicit approval each time)

1. Connect the Git repository (`AI-Consulting-Business`, this `website/`
   directory as the project root) to a Vercel account/team.
2. In Project Settings > Environment Variables, add every variable listed
   in `.env.example`, scoped separately for **Development**, **Preview**,
   and **Production** — do not reuse live Stripe keys in Preview.
3. Deploy Preview first. Run the acceptance checklist in
   `14_CLAUDE_IMPLEMENTATION/ACCEPTANCE_CRITERIA.md` and
   `14_CLAUDE_IMPLEMENTATION/TEST_PLAN.md` against the Preview URL.
4. Only after the owner reviews the Preview and approves: add the custom
   domain (see `IONOS_DNS_PLAN.md`) and promote to Production.
5. Record the deployed commit SHA and Vercel deployment URL in
   `IMPLEMENTATION_REPORT.md`, and know the rollback path (Vercel keeps
   prior deployments; "Promote" an earlier one if a post-launch check
   fails).

## Why this session didn't deploy

This implementation session has a Vercel MCP connector available, but
deploying — even to Preview — creates a live, reachable URL under the
owner's account and is a "publish" action, so it needs the owner's explicit
in-chat approval each time (not implied by the original build request).
Ask before running it.

## Deploy attempt (this session)

With the owner's approval, this session attempted a direct-file Preview
deployment via the Vercel MCP connector to team `EchoFrame's projects`
(`team_aRAPqQAKxNgEEADhOrrt1byO`), project name `practical-ai-operations`.

**Result: blocked.** Both attempts (explicit team ID, and no team ID) failed
with:

```
Vercel API error 403: {"error":{"code":"forbidden","message":"You don't have
permission to create a project.","action":"View Documentation",
"link":"https://vercel.com/docs/accounts/team-members-and-roles"}}
```

This is a Vercel account/role permission limit on the connected integration
- not a code or configuration problem in this repo. The owner needs to
either grant project-creation permission to whatever role this session's
Vercel connector is using, or create the Vercel project themselves (via the
Vercel dashboard or `vercel` CLI logged in as an authorized member) and
connect this repository to it. Everything else in this doc still applies
once a project exists.
