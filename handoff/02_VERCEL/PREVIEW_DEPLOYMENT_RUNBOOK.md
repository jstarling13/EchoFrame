# Preview Deployment Runbook

**Purpose:** Deploy only after project and minimum variables exist

**Version:** 1.0 | **Date:** 2026-08-29

## First deployment

Push/redeploy `website-implementation`; confirm it produces a Preview URL, not Production. Record deployment ID, commit SHA, branch, build logs, and environment.

## Minimum useful Preview

Routes can be reviewed without Stripe. Contact submission must not falsely succeed if both email and CRM are unavailable. Payment and webhook testing wait for their variables.

## Preview protections

Robots disallow/noindex; legal pages always noindex and display attorney-draft banner; test Stripe only; no custom domain; no client sensitive information; structured logs exclude free-text form contents.

## Return

URL, commit SHA, routes/build status, variable names configured (never values), service readiness, test evidence, screenshots, risks, and owner review checklist.
