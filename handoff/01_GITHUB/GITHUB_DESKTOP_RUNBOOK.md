# GitHub Desktop Runbook

**Purpose:** Publish the existing clean repository without installing Homebrew or GitHub CLI

**Version:** 1.0 | **Date:** 2026-08-29

## Install

Download GitHub Desktop from `https://desktop.github.com/`, install, and sign into the correct GitHub account through the browser. Never give credentials or browser codes to Claude.

## Add local repository

File → Add Local Repository → `/Users/jacob/AI-Consulting-Business`. Confirm GitHub Desktop recognizes existing history and no uncommitted changes.

## Publish main first

Switch Current Branch to `main`. Click Publish Repository. Name `white-oak-operations`; description `White Oak Operations business platform and website`; Keep this code private checked; select the intended owner/organization.

## Publish implementation

Switch to `website-implementation`; click Publish branch; keep it checked out. Do not merge.

## Claude verification

Run `git remote -v`, `git branch -vv`, `git status`, `git ls-remote --heads origin`, and record repository URL, remote tracking, current branch, and HEAD. No pull/push/merge during verification.
