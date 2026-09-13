# Case Study Deep Draft

## Editorial status

Draft for Jacob Starling’s review. Do not publish any item marked `[CONFIRM WITH JACOB]` until Jacob has confirmed it. The client must remain anonymous. Do not name SRG Business Services LLC, Dunkin’, Baskin-Robbins, or disclose the client’s revenue.

## Proposed public title

# From Three 16-Hour Processing Days to Six Hours a Week

## Proposed standfirst

A multi-location food-service accounting operation relied on one person to complete a weekly reconciliation and posting process by hand. EchoFrame rebuilt the workflow around QuickBooks Desktop’s supported integration path, reducing client-tracked processing time from approximately 48 hours to approximately six hours per week. `[CONFIRM WITH JACOB]`

## At a glance

| Measure | Before | After | Evidence status |
|---|---:|---:|---|
| Weekly processing time | Approximately 48 hours | Approximately 6 hours | Client-tracked; `[CONFIRM WITH JACOB]` |
| Schedule | Three 16-hour processing days | Approximately two hours on each of those three days | Client-tracked; `[CONFIRM WITH JACOB]` |
| Reduction | 42 hours per week | 87.5% | Calculated from client-tracked inputs; `[CONFIRM WITH JACOB]` |
| Locations supported | 13 | 13 | `[CONFIRM WITH JACOB]`; potentially identifying |
| Initial build time | Approximately 2.5 days | Not applicable | Founder-reported; `[CONFIRM WITH JACOB]` |
| Implementation fee | $650 total | Not applicable | Do not publish by default; `[CONFIRM WITH JACOB]` |
| Initial accuracy | Approximately 80% before fine-tuning | Current rate not formally measured | Founder estimate; do not use as a performance claim |
| Observation period | June 2026 | September 2026 | Approximately three months; `[CONFIRM WITH JACOB]` |

## The operating problem

The client supported the accounting process for a multi-location food-service business. Each week, one person manually moved information into QuickBooks and completed the related reconciliation and posting work. The process consumed three 16-hour days, or approximately 48 hours each week. `[CONFIRM WITH JACOB]`

That burden was not merely an inconvenience. It concentrated an important financial process in one person, limited the capacity available for other clients and higher-value review, and made the operation dependent on long manual processing days.

The goal was not to “add AI” in the abstract. It was to remove repeatable data-entry work while keeping the accounting operator in control of review and exceptions.

## Scope and intervention

EchoFrame built a full-stack accounting synchronization system using a SOAP service and the QuickBooks Web Connector protocol. The system generated store-level qbXML journal-entry requests and posted them through QuickBooks’ integration workflow, replacing the repeated manual creation of those entries.

The implementation covered 13 locations. `[CONFIRM WITH JACOB]` The initial build was completed in approximately 2.5 days. `[CONFIRM WITH JACOB]`

Before publication, add a precise, non-sensitive description of:

- the upstream source or sources from which transaction data originated: `[BRACKETED PLACEHOLDER: DATA SOURCES]`;
- the reconciliation rules applied before posting: `[BRACKETED PLACEHOLDER: RECONCILIATION LOGIC]`;
- the human approval or exception-review step: `[BRACKETED PLACEHOLDER: CURRENT REVIEW CONTROL]`;
- the failure notification and recovery path: `[BRACKETED PLACEHOLDER: FALLBACK PROCEDURE]`.

## What changed

From June through September 2026, the client tracked approximately six hours of weekly processing time after implementation, compared with approximately 48 hours before implementation. `[CONFIRM WITH JACOB]` On those inputs, the workflow reclaimed approximately 42 hours per week, an 87.5% reduction.

That figure is a time-capacity result, not a guaranteed cash saving. EchoFrame has not established that 42 reclaimed hours produced a corresponding reduction in payroll or operating expense. The more accurate conclusion is that the system returned substantial weekly capacity to the operator.

## Measurement method

1. **Baseline:** The client tracked one person working three 16-hour days on the manual process, approximately 48 hours per week. `[CONFIRM WITH JACOB]`
2. **Post-implementation:** The client tracked approximately two hours on each of the same three processing days, approximately six hours per week. `[CONFIRM WITH JACOB]`
3. **Calculation:** `(48 - 6) / 48 = 87.5%`.
4. **Observation window:** Approximately June through September 2026. `[CONFIRM WITH JACOB]`
5. **Attribution:** The figures were tracked by the client and relayed to EchoFrame. They were not independently audited.

## What the result does not prove

- This is one implementation for one client.
- The time figures were client-tracked but not independently audited.
- No formal pre/post error-rate study was conducted.
- The initial version was estimated by Jacob to be approximately 80% accurate and required fine-tuning; the current accuracy rate is unknown.
- No claim is made that reclaimed time equals realized cash savings.
- No claim is made that another business will achieve the same result.
- The client and franchise brands are intentionally anonymized.
- The system’s performance may depend on the client’s specific data structure, QuickBooks configuration, operating discipline, and exception volume.

## What this case demonstrates

The useful lesson is not that every accounting process can be reduced by 87.5%. It is that a measurable workflow, with stable inputs and repeatable posting logic, can be redesigned around the work actually being done. The intervention began with the process, used the existing accounting system’s integration path, and retained human involvement for the work that still required review.

## Recommended public proof block

**Approximately 42 hours of weekly processing capacity reclaimed.**

For one anonymized multi-location accounting operation, EchoFrame reduced a client-tracked manual workflow from approximately 48 hours to approximately six hours per week over a three-month observation period. The figures were not independently audited, no formal error-rate study was conducted, and results will vary by workflow. `[CONFIRM WITH JACOB]`

## Required correction to the current website

The current homepage states “five hours a day” and describes 15 locations. Those claims conflict with Jacob’s current account of 13 locations and a reduction from 48 to six hours per week. Claude must not merge the versions. Replace the old claim only after Jacob confirms the 13-location, 48-to-six-hour figures in writing and obtains the client’s confirmation. Until then, use a qualitative statement with no numerical reduction.
