# EchoFrame QA & Acceptance Checklist

## Functional
- intended trigger works
- expected happy-path output is correct
- duplicate event behavior tested
- missing-data behavior tested
- exception path tested
- failure notifications tested
- permissions tested

## Data
- source of truth confirmed
- field mappings validated
- no unintended cross-entity mixing
- sample outputs checked by client process owner
- sensitive data exposure reviewed

## Human Controls
- required approvals remain in place
- AI output clearly distinguishable from authoritative records where needed
- no autonomous professional judgment outside scope
- exception owner identified

## Operations
- owner can run workflow
- restart/recovery procedure documented
- credential ownership documented
- billing/API dependencies documented
- external vendor dependencies listed

## Acceptance Evidence
Capture:
- screenshots or logs
- sample records
- client sign-off notes
- unresolved known limitations

## Launch Decision
Go live only when:
- critical tests pass
- client process owner approves
- access/security conditions are satisfied
- rollback/manual fallback exists for important workflows
