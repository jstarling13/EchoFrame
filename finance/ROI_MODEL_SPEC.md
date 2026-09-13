# EchoFrame ROI Model Specification

## Purpose
Create a conservative internal calculator that compares implementation cost with measurable operational value.

This should support proposals and prioritization, not produce guaranteed-savings claims.

## Inputs

### Labor
- workflow frequency
- occurrences per week/month
- average minutes per occurrence
- number of employees involved
- loaded hourly cost or user-supplied wage assumption
- percentage of time realistically reducible

### Error / Rework
- average error frequency
- average correction time
- direct monetary error cost if known
- percentage realistically avoidable

### Delay / Revenue
Only include if supportable:
- leads per period
- response-time issue
- observed conversion / loss data
- conservative improvement assumption

Avoid speculative revenue claims.

### Current Tool / Vendor Cost
- software
- contractor
- temporary labor
- other recurring operating cost

### EchoFrame Cost
- estimated consulting hours × $40
- travel
- stipend
- approved software/API cost
- expected ongoing maintenance

## Calculations

### Current Annual Labor Cost of Workflow
frequency × time per occurrence × loaded labor rate × annual periods

### Estimated Annual Labor Capacity Reclaimed
current labor cost × conservative reducible percentage

### Annual Avoided Rework
current rework cost × conservative reducible percentage

### Annual Recurring Tool/Vendor Savings
only where an existing expense is actually removed

### Year-One Gross Value
capacity reclaimed + avoided rework + validated recurring savings + validated incremental contribution

### Year-One Implementation Cost
EchoFrame labor + travel + stipend + implementation software + first-year maintenance estimate

### Net Year-One Value
gross value - year-one implementation cost

### Simple Payback Period
implementation cost / monthly recurring value

## Output
Show three scenarios:
- Conservative
- Expected
- Upside

The proposal should lead with the conservative or expected case, not upside.

## Required Caveat
Recovered employee time is capacity, not automatically cash savings.
Do not equate reclaimed hours with payroll reduction unless the client specifically plans to eliminate or avoid a cost.

## Suggested Spreadsheet Tabs
1. Inputs
2. Workflow Economics
3. Implementation Cost
4. Scenario Summary
5. Assumptions & Notes
