# Data, Human Review, and Escalation

**Purpose:** Embed safety into workflow design

**Version:** 1.0 | **Date:** 2026-08-28

## Internal knowledge

Use approved, current, access-controlled sources; record source owners and freshness; prevent retrieval across unauthorized groups; cite source locations; define removal and re-indexing.

## Sensitive information

Minimize inputs; redact/tokenize where useful; confirm vendor terms, training/retention settings, residency, subprocessors, access, logging, deletion; prohibit secrets in prompts; use test/synthetic data first.

## Human review tiers

Tier 0 formatting/low consequence: sampling. Tier 1 internal draft: accountable reviewer before use. Tier 2 external or material commitment: qualified reviewer and logged approval. Tier 3 regulated/safety/consequential: specialist governance; no autonomous release by default.

## Verification

Schema validation, source citation, deterministic calculations, business-rule checks, comparison to system of record, confidence/coverage flags, sample QA, and user confirmation. Do not rely on self-critique alone.

## Escalation

Stop and route when data is unauthorized, output affects rights/safety/finances, confidence or evidence is insufficient, instructions conflict, integration fails, or user attempts prohibited use. Log owner, severity, containment, decision, and corrective action.
