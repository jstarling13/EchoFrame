# Model Selection Framework

**Purpose:** Select models and architectures by evidence, not allegiance

**Version:** 1.0 | **Date:** 2026-08-28

## Candidate architectures

Single model; model with retrieval; tool/API calling; deterministic automation with model step; multi-model sequential review; parallel model comparison; manual handoff; no-model rules/template.

## Weighted criteria

Task quality 25%; instruction reliability 10%; factual grounding/verification 10%; privacy/security/admin controls 15%; integration/tool fit 10%; latency 5%; unit economics 10%; context/file fit 5%; accessibility/usability 5%; portability/exit 5%. Adjust weights with documented rationale.

## Test protocol

Create representative gold set and failure cases; blind outputs where practical; score with rubric; measure latency/cost; test refusal, prompt injection, malformed files, missing context, and sensitive data behavior; record model/version/date/settings. Re-test on material model or workflow changes.

## Multi-model use

Use only when independent strengths or review reduce a measured failure mode. Define what passes between models, which system is authoritative, disagreement handling, cost/latency ceiling, and human escalation. Two models agreeing is not proof.

## Fallback

Every production workflow states behavior for outage, timeout, low confidence, invalid output, failed integration, and human rejection. Fallback may be manual processing, queued work, deterministic template, alternate approved model, or safe stop.
