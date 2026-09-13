# EchoFrame AI Governance Baseline

## 1. Human Accountability
AI output is not treated as authoritative merely because it is generated confidently.

Every workflow must identify:
- system owner
- human reviewer
- approval threshold
- exception owner

## 2. Data Minimization
Use only the data required for the workflow.

Do not send sensitive information to a model or vendor without:
- client authorization
- appropriate vendor terms
- a documented reason
- access controls
- an understood retention path

## 3. High-Risk Boundaries
Do not provide autonomous:
- clinical decisions
- legal advice
- investment recommendations
- lending/underwriting decisions
- employment screening decisions
- safety-critical control
- financial commitments / payments without approved human control

## 4. Least Privilege
Use the lowest permissions necessary.
Avoid shared credentials.
Use MFA where available.

## 5. Auditability
For material actions, preserve:
- timestamp
- actor/system
- input/reference
- output/action
- approval where required

## 6. Testing
Before launch:
- happy path
- missing data
- duplicate events
- bad input
- edge cases
- model uncertainty
- vendor/API outage behavior
- rollback/manual fallback

## 7. Client Ownership
Clients should understand:
- what the workflow does
- what tools it depends on
- how to stop it
- where human review occurs
- what ongoing maintenance may be required

## 8. Model Changes
Do not swap models in production solely because a newer model exists.
Re-test material workflows before changing a production dependency.

## 9. Professional Review
Where accounting, legal, clinical, security, or other professional judgment is required, use the appropriate human professional.
