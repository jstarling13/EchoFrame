# CRM and Client Folder Specification

**Purpose:** Create traceable commercial and delivery records

**Version:** 1.0 | **Date:** 2026-08-28

## CRM fields

Account ID, name, domain, industry, geography, headcount band, source/referrer, contacts/roles, CLEAR score, stage, need, workflow, value category, risk/data class, offer, amount, probability, next action/date, lost reason, consent, last contact.

## Client structure

/CLIENT_ID_Name/00_Admin; 01_Contract; 02_Intake; 03_Discovery; 04_Design; 05_Build; 06_Test; 07_Training; 08_Launch; 09_Reports; 10_Handoff; 99_Archive. Sensitive evidence stays in approved secure client storage, not duplicated automatically.

## Naming

YYYYMMDD_CLIENTID_WORKFLOW_ARTIFACT_vMAJOR.MINOR_STATUS.ext. Status: DRAFT, REVIEW, APPROVED, SUPERSEDED. Never use “final_final.”

## Project ID

WOO-YYYY-NNN (updated from PAO- upon company name confirmation, see `strategy/DECISION_LOG.md`). Workflow ID: client ID + WF-NNN. Prompt/instruction ID: workflow + INS-NNN. Stripe metadata uses these stable IDs.
