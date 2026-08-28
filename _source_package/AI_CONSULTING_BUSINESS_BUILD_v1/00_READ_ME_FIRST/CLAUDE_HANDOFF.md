# Claude Code Handoff

**Purpose:** Give the local implementation agent a concise starting contract

**Version:** 1.0 | **Date:** 2026-08-28

## Instruction

Treat this archive as the authoritative v1 business specification. First inspect local files and Git state. Do not overwrite existing work without comparing content and preserving stronger components.

## Required reading

00_READ_ME_FIRST/*, then 14_CLAUDE_IMPLEMENTATION/MASTER_CLAUDE_PROMPT.md and the acceptance/test plans.

## Do not assume

The working brand is cleared; products exist in Stripe; environment variables exist; Vercel is connected; IONOS DNS is safe to change; legal drafts are approved; or website starter files match the local framework.

## Definition of done

A reviewed repository, passing tests, accessible preview, Stripe test-mode end-to-end payment, verified webhook processing, preserved DNS/email records, documented deployment, and acceptance evidence. Production launch requires explicit owner approval.
