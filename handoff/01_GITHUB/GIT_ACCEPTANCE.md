# Git Acceptance Criteria

**Purpose:** Gate Vercel import

**Version:** 1.0 | **Date:** 2026-08-29

## Pass

Private repository; correct owner; `origin` points to intended repo; remote `main` and `website-implementation`; local tracking correct; current branch `website-implementation`; working tree clean; no secrets or `.env*`; history preserved.

## Fail

Public repository, wrong account, only one branch, initialized unrelated history, merge performed, credentials committed, or local changes introduced. Stop and report; do not force-push or destructively reset.
