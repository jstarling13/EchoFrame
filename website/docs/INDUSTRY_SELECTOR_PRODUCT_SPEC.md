# EchoFrame Industry Selector — Product Specification

## Goal
Create a polished, low-friction interaction that helps a visitor recognize themselves and see relevant EchoFrame capabilities.

This is not a lead form and not an automated consulting diagnosis.

# Step 1 — Industry

## Heading
**What kind of business are you running?**

Supporting text:
Choose the closest fit. The workflow matters more than the label.

## Primary Buttons
- Accounting & Bookkeeping
- Professional Services
- Real Estate & Property
- Construction & Trades
- Retail & Multi-Location
- Recruiting & Staffing
- Multi-Entity Businesses
- Other

Optional `View all` only if more industries are later added.

# Step 2 — Workflow Problem

## Heading
**What is taking too much time?**

## Buttons
- Financial Workflows
- Repetitive Admin
- Customer Follow-Up
- Reporting & Visibility
- Multi-Entity Complexity
- Document Intake
- Staff AI Use
- I'm Not Sure Yet

# Step 3 — Result

## Heading
**A practical place to start**

Output should combine:
- selected industry
- selected problem
- 2–3 relevant EchoFrame capabilities
- one sentence on likely first diagnostic question
- CTA

Example:
Accounting & Bookkeeping + Financial Workflows

**Start with the repetitive work around the judgment.**

Possible starting points:
- deposit matching and exception queues
- reconciliation support
- document/client-request intake

First question:
Where is the same information being matched, checked, or re-entered by hand?

CTA:
**Talk Through This Workflow**

# Interaction
- step 2 appears after step 1 selection
- selected chip has clear state
- result appears after step 2
- user can change either selection without resetting the entire page
- URL query parameters are optional but useful for shareable state
- no forced form
- CTA can prefill non-sensitive context such as industry/problem on Contact page

# Data
Do not put free-text sensitive data into URL params.

Allowed example:
`?industry=accounting&problem=financial-workflows`

# Mobile
Pills wrap naturally. Do not create horizontal-scroll-only controls.

# Visual Character
- oversized consulting-style heading
- lots of whitespace
- rounded pills/buttons
- restrained border
- strong type hierarchy
- minimal icon use
- EchoFrame palette, not Bain red

# Copy Rule
Do not claim `we specialize in` an industry unless there is sufficient real experience.

Use:
`Common workflows we can evaluate in...`
or
`Where EchoFrame can help...`
