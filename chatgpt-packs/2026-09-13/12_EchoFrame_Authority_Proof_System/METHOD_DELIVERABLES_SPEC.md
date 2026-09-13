# OWNED Method Deliverables Specification

The public Method page currently names five stages but does not show what the client receives. Each stage below adds one concrete primary deliverable, acceptance criteria, and the decision it supports.

## 1. Observe

### Deliverable: Current-State Workflow Record

A concise visual and written record of how the selected workflow actually operates today, including trigger, inputs, systems, handoffs, decisions, exceptions, outputs, owners, volume, timing, and known pain points.

**Minimum contents**

- start and end boundaries;
- step-by-step workflow map;
- systems and data touched;
- named role responsible for each step;
- observed timing and frequency;
- exception paths and workarounds;
- open facts that still need verification.

**Acceptance test:** The people who perform the work recognize the map as accurate and correct any material omissions.

**Decision enabled:** Are we solving the real workflow or an idealized description of it?

## 2. Weigh

### Deliverable: Opportunity and Risk Scorecard

A ranked assessment of the workflow’s potential value and implementation risk, supported by documented assumptions rather than a generic “AI opportunity” label.

**Minimum contents**

- baseline labor and cycle time;
- error, delay, concentration, and compliance exposure;
- data sensitivity and required approvals;
- estimated value range, with capacity separated from cash savings;
- feasibility, dependency, and maintenance assessment;
- automate, assist, defer, or decline recommendation.

**Acceptance test:** Every claimed benefit traces to a baseline or is labeled as an assumption; every material risk has an owner or blocks the build.

**Decision enabled:** Is this workflow worth changing now?

## 3. Navigate

### Deliverable: Solution Architecture and Control Plan

A vendor-neutral design showing how data will move, which tools will perform each function, where human judgment remains, and how the client can exit or replace each dependency.

**Minimum contents**

- system and data-flow diagram;
- build-versus-buy choices and rationale;
- permissions and data-minimization plan;
- human review and approval thresholds;
- exception, logging, retention, and failure paths;
- operating cost and vendor dependencies;
- ownership and exit plan.

**Acceptance test:** The client can see what enters each system, what leaves it, who approves material actions, and how the workflow stops safely.

**Decision enabled:** What is the smallest defensible architecture?

## 4. Engineer

### Deliverable: Tested Production Workflow

The implemented workflow plus its test record, configured controls, monitoring, exception queue, and manual fallback.

**Minimum contents**

- working integration or automation;
- versioned configuration and access list;
- tests for normal, missing, duplicate, malformed, and delayed inputs;
- vendor/API outage and rollback tests;
- action logs and error notifications;
- issue register with resolution status;
- launch checklist and approval.

**Acceptance test:** Agreed tests pass, known limitations are documented, and the named owner can stop the workflow and use the fallback.

**Decision enabled:** Is this safe and reliable enough to enter live use?

## 5. Demonstrate & Transfer

### Deliverable: Performance and Ownership Handoff Pack

A single package proving what changed and giving the client what it needs to operate, troubleshoot, maintain, and extend the workflow without permanent dependence on EchoFrame.

**Minimum contents**

- before-and-after measurement report;
- limitations and unresolved risks;
- standard operating procedure;
- exception and recovery guide;
- role-based training materials;
- credential, vendor, and asset inventory;
- maintenance schedule and change log;
- ownership acceptance sign-off.

**Acceptance test:** The client’s designated owner completes a supervised run, handles a test exception, demonstrates the fallback, and confirms receipt of the assets and documentation.

**Decision enabled:** Can the client operate this system independently, and did the engagement produce a measurable result?

## Recommended Method-page summary

| Stage | What EchoFrame does | What the client receives |
|---|---|---|
| Observe | Maps the work as it actually happens | Current-State Workflow Record |
| Weigh | Tests value against operating risk | Opportunity and Risk Scorecard |
| Navigate | Designs the data path, controls, and ownership model | Solution Architecture and Control Plan |
| Engineer | Builds and tests the live workflow | Tested Production Workflow |
| Demonstrate & Transfer | Measures performance and transfers operation | Performance and Ownership Handoff Pack |
