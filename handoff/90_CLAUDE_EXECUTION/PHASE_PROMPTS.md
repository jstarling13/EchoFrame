# Phase Prompts

**Purpose:** Provide short continuation prompts after each owner action

**Version:** 1.0 | **Date:** 2026-08-29

## After GitHub Desktop publication

Verify `origin`, private owner/repo, remote main and website-implementation, tracking, clean tree, current branch. Do not push/pull/merge. Return repository URL and evidence.

## After Vercel project creation

Verify project exists, Git connection, Root Directory `website`, Production branch `main`. Classify environment variables by phase. Do not request values or deploy.

## After Preview variables confirmed

Deploy `website-implementation` as Preview only. Record URL/commit/deployment. Run basic route/noindex/legal/security QA. Return remaining service blockers.

## After Stripe/Upstash/Resend configured

Run full payment, webhook, durable-store, contact delivery, failure, performance, accessibility, browser, and responsive matrix. Return PREVIEW-READY or BLOCKED.

## After owner Preview approval and professional gates

Prepare reviewed PR and production plan. Do not merge, create live objects, change IONOS, or deploy until each specific action is explicitly approved.
