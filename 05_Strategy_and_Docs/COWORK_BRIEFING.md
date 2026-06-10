# BUSINESS CLARITY PLATFORM — MASTER BRIEFING DOCUMENT
### For Claude Cowork — Full Context + Overnight Task List
**Owner:** Jacob | **Date:** May 2026 | **Goal:** $50k in 90 days

---

## WHO I AM + WHAT WE'RE BUILDING

I am Jacob. I am a Master of Finance graduate (Emory University, Goizueta Business School, graduating May 2026), Investment Analyst at Blue Eagle Capital, and commissioned Navy officer starting August 2026. I have roughly 90 days to generate $50k before I report to OCS. I am building a business to do this.

The business is called the **Business Clarity Platform**. It is an AI-powered service that transforms raw financial and operational data from small businesses into plain-English insights, specific recommendations, and formatted deliverables — things that look like they cost $3,000–5,000 from a consultant but are produced using AI agents in 1–2 hours per client.

My role is CEO and sales only. I find the clients. The AI builds everything. I deliver the product.

---

## WHAT HAS ALREADY BEEN BUILT

### 1. The Revenue Engine Dashboard (Fully Functional)
A browser-based HTML/React artifact (built in Claude.ai) with 5 AI-powered agents. Each agent takes a short intake form and generates a full client deliverable using the Anthropic API. The user copies the output, pastes it into a new Claude chat, and converts it to a Word doc or PDF.

**Agent 1: Monthly Financial Narrative Report** — $300–500/month
- Input: Business name, industry, revenue, expenses, expense categories, prior month revenue, owner concerns
- Output: Plain-English 12–15 page report with executive summary, revenue analysis, expense breakdown, top 5 expense leaks, cash flow snapshot, 90-day projection, and one specific recommendation

**Agent 2: Business Audit Package** — $750–1,000 one-time
- Input: Business name, industry, location, years in business, employees, monthly revenue, last 3 months financials, top competitors, main challenge
- Output: 20–25 page audit with business health score (graded out of 100), financial health analysis, market position analysis, operational efficiency assessment, top 3 ROI-ranked recommendations, and 5 quick wins

**Agent 3: SOP & Employee Handbook** — $500–800 one-time
- Input: Business name, type, owner name, employee count, roles, key processes, common mistakes, culture description
- Output: Complete Word-ready handbook with welcome letter, 5 core values, 30-day onboarding plan, role-specific SOPs, customer service scripts, opening/closing checklists, and basic policies

**Agent 4: Custom Excel Dashboard** — $600–900 one-time
- Input: Business name, type, Excel comfort level, current tracking method, revenue streams, expense categories, what owner wants to understand
- Output: Full specification with exact tab names, column headers, Excel formulas (exact syntax), color-coding thresholds, and owner quick-start guide — ready to hand to a new Claude chat to build the actual .xlsx file

**Agent 5: Competitor Intelligence Report** — $400–600 one-time
- Input: Business name, type, city/state, goal, top 3–5 competitors described, client strengths, client weaknesses
- Output: 15-page competitor report with landscape overview, competitor profiles, competitive scorecard (1–5 rating table), where client is winning, where client is losing, 3 things to steal from competitors, and 90-day competitive action plan

### 2. Apollo.io Prospect Puller (Fully Functional)
A Streamlit Python app (`apollo_scraper.py`) that hits the Apollo.io API to pull verified small business owner contacts. Filters by city, state, industry, company size (1–50 employees), and title (Owner, Founder, CEO, President). Outputs a CSV with name, title, email, phone, LinkedIn, company, industry, and website. Auto-highlights priority targets (verified email + phone). Generates a templated cold outreach email from the results. I have an Apollo.io API key and an active account.

---

## THE PRODUCT STRATEGY (FULL CONTEXT)

### Core Positioning
**"Business Clarity Platform gives small business owners the financial intelligence of a $400/hr consultant — automated, in plain English, delivered before the problem gets expensive."**

This is NOT a financial reporting tool. It is not accounting software. It is a decision-making tool. Owners don't need more data — they need to know what the data means and what to do about it.

### Target Customers (in priority order)
1. **Home service businesses** — HVAC, plumbers, electricians, roofers, landscapers. Columbus, GA and surrounding areas first, then scale geographically. They make real money ($500k–$2M/year), have zero financial sophistication, and pay cash.
2. **Salons and barbershops** — High volume, owner-operated, strong pain around payroll and product costs
3. **Restaurants** — Cash flow problems are existential. They need this.
4. **Contractors** — Job-level profitability analysis is their biggest need
5. **Agencies (marketing, dev)** — Higher sophistication but higher willingness to pay

### Pricing Model
- **Monthly retainer (anchor product):** $300–500/month per client — Monthly Financial Narrative Report
- **One-time deliverables (cash injection):** $400–1,000 per project — Audits, SOPs, Competitor Reports, Excel Dashboards
- **Target:** 20 monthly retainer clients = $6,000–10,000/month recurring + one-time projects on top

### Revenue Math to $50k in 90 Days
- Month 1: Close 5 retainer clients ($2,000/mo) + 5 one-time projects (~$3,500) = ~$5,500
- Month 2: Grow to 15 retainer clients ($6,000/mo) + more one-time = ~$10,000
- Month 3: 20+ retainer clients ($8,000/mo) + pipeline of one-time = ~$12,000+
- Cumulative: ~$27,500 in recurring + ~$15,000–25,000 in one-time = $42,000–52,000

### Why Clients Can't DIY This
- They don't know which numbers matter
- They don't know what industry benchmarks to compare to
- They don't have time
- They can't write — producing a 15-page report from scratch would take them 20 hours
- What takes them 20 hours takes me 90 minutes with the AI pipeline

### The Sales Motion
1. Pull prospect list from Apollo (done — tool is built)
2. Cold outreach via email + phone (script below)
3. Offer a FREE sample report for their specific business as the hook
4.15-minute call — show the sample, let the deliverable sell itself
5. Close at $400/month or one-time price

**Cold email script:**
> Subject: Free financial clarity report for [Company Name]
>
> Hi [First Name],
>
> I work with [industry] businesses in [city] to produce a monthly plain-English breakdown of exactly where their money is going — no accountant jargon, just what's happening and what to do about it.
>
> I put together a free sample for a business like [Company Name]. Most owners find at least one thing worth acting on immediately.
>
> Worth 15 minutes this week?
>
> [Name] | [Phone]

---

## SYSTEM ARCHITECTURE (HOW EVERYTHING WORKS)

### Current Workflow (Manual, What Exists Now)
```
Client intake (form or call)
→ Jacob enters data into Revenue Engine dashboard
→ Dashboard calls Anthropic API with structured system prompt
→ AI generates full report content
→ Jacob copies output → pastes into new Claude chat
→ Claude converts to formatted Word doc or PDF using docx/pdf skills
→ Jacob emails finished document to client
```

### Target Workflow (What to Build Toward)
```
Client submits CSV or connects QuickBooks
→ Auto-parsed into universal financial schema
→ Business type detected → correct benchmarks loaded
→ Insight engine runs (rules + trend detection + AI reasoning)
→ Formatted report auto-generated as PDF
→ Auto-emailed to client on the 1st of each month
→ Jacob reviews and approves before send (optional)
```

### The Insight Engine Logic
Three layers that run in order:
1. **Rules layer (deterministic math):** Calculate every financial ratio. Flag anything outside industry benchmark range. This runs first and produces structured flags — not AI.
2. **Trend layer:** Compare flagged metrics to prior periods. Classify as improving / stable / deteriorating. Detect velocity.
3. **AI reasoning layer:** Pass flags + trends + business context to Claude API. Claude explains what the combination means in plain English, generates specific recommendations tied to actual numbers, and writes the narrative.

### Industry Benchmark Thresholds (Key Reference)
| Metric | Home Services | Agency | Ecommerce | Professional Services |
|--------|--------------|--------|-----------|----------------------|
| Payroll % | 25–35% | 50–65% | 8–15% | 35–50% |
| COGS % | 20–35% | 5–15% | 40–65% | 5–20% |
| Primary risk | Job margin | Utilization rate | CAC payback | Realization rate |
| Cash cycle | 30–45 days | 45–90 days | 15–30 days | 60–90 days |

---

## PRODUCT EVOLUTION ROADMAP

### Stage 1 (NOW — Weeks 1–6): Manual Pipeline, First Revenue
What exists: Revenue Engine dashboard + Apollo scraper
Goal: 10 paying clients, $4,000–6,000 MRR
What to build: Sample demo reports, landing page, outreach sequences

### Stage 2 (Weeks 6–12): Semi-Automated Intake
What to add: CSV upload → auto-parsing into financial schema, basic client management spreadsheet
Goal: Reduce time per client from 90 min to 30 min
Tech: Python script that parses QuickBooks CSV export into standard fields, auto-populates the intake form

### Stage 3 (Weeks 12–20): Connected Data + Recurring Delivery
What to add: QuickBooks API integration, Xero API, automated monthly report generation, email delivery
Goal: Clients set it and forget it. Report arrives in inbox on the 1st.
Tech: OAuth integration, scheduled Python job, Resend or SendGrid for delivery

### Stage 4 (Month 6+): Client Portal + Benchmarking
What to add: Client login, historical trend dashboard, industry benchmarking database, white-label option for accountants/bookkeepers
Goal: $50k+ MRR, sell to accounting firms as a tool they resell

---

## TONIGHT'S TASK LIST FOR COWORK

These are the specific deliverables I need built while I sleep. Work through them in order. Each task is self-contained.

---

### TASK 1: Build 3 Sample Demo Reports (HIGHEST PRIORITY)
I need polished sample reports to show prospects on sales calls. These must look real — use fictional but realistic business names and numbers.

**Sample Report A — Home Services (HVAC)**
Business: "Comfort Zone HVAC" — Birmingham, AL — 8 employees — $72,000/month revenue
Financials: Payroll $22,000 | Materials $18,000 | Trucks/fuel $4,200 | Insurance $2,100 | Rent $1,800 | Marketing $1,400 | Misc $2,800 | Total expenses $52,300
Prior month revenue: $68,000
Concerns: "We're always busy but I never have cash. I think some of our jobs aren't profitable but I don't know which ones."

Generate using the Monthly Financial Narrative Report agent system prompt. Then format as a professional Word document with:
- Cover page: Business name, "Monthly Financial Clarity Report," month/year, "Prepared by Business Clarity Platform"
- Section headings in dark navy (#1F2D40)
- Page numbers
- Clean professional layout

Save as: `sample_report_hvac.docx`

**Sample Report B — Restaurant**
Business: "Fork & Fire Kitchen" — Columbus, GA — 14 employees — $89,000/month revenue
Financials: Payroll $31,000 | Food/beverage COGS $28,500 | Rent $6,200 | Utilities $3,100 | Marketing $1,800 | Insurance $1,400 | Misc $2,200 | Total expenses $74,200
Prior month revenue: $94,000
Concerns: "Revenue dropped this month and I have no idea why. Food costs feel high but I don't have time to track it properly."

Same format. Save as: `sample_report_restaurant.docx`

**Sample Report C — Salon**
Business: "Elevate Salon & Spa" — Atlanta, GA — 9 employees — $41,000/month revenue
Financials: Payroll $18,500 | Product/supplies $4,800 | Rent $4,200 | Marketing $1,200 | Insurance $900 | Misc $1,400 | Total expenses $31,000
Prior month revenue: $38,500
Concerns: "I added two new stylists but profit didn't go up. I don't understand why."

Same format. Save as: `sample_report_salon.docx`

---

### TASK 2: Build a One-Page Landing Page (HTML)
Build a single clean HTML landing page for the Business Clarity Platform. This is the page I send to prospects after the cold email reply, before the call.

**Design requirements:**
- Background: white (#FFFFFF)
- Accent color: amber/gold (#D97706)
- Font: Inter or system-sans
- Clean, minimal, professional — NOT startup-flashy
- Mobile responsive

**Content to include (exact copy):**

HEADLINE: "Finally know what's actually happening in your business."

SUBHEADLINE: "Plain-English financial reports that tell you where your money is going, what's leaking, and exactly what to fix — delivered every month."

BEFORE/AFTER SECTION:
Before — "Your accountant hands you a P&L you don't fully understand. You make decisions on gut feel. You find out about problems 60 days after they start."
After — "Every month you get a clear report: what happened, what it means, and the one thing to do about it. In plain English."

THREE PRODUCT CARDS:
1. Monthly Clarity Report — $399/month — "Plain-English monthly breakdown of your financials with specific recommendations"
2. Business Audit — $799 one-time — "Full health check of your business with a scored assessment and ranked action plan"
3. Competitor Report — $499 one-time — "See exactly where you stand vs. your top competitors and what to do about it"

SOCIAL PROOF PLACEHOLDER: Three quote boxes with "[Industry] business owner, [City]" attribution — write realistic-sounding testimonials about the value of plain-English financial clarity

CTA: "Get a free sample report for your business" — button links to mailto: (leave email placeholder)

FOOTER: "Business Clarity Platform | Not accounting software. Business intelligence."

Save as: `landing_page.html`

---

### TASK 3: Write the Full Outreach Sequence (5 emails + 2 LinkedIn messages)
Write a complete cold outreach sequence for home service business owners (HVAC, plumbers, electricians). This is what I send after pulling the Apollo prospect list.

**Email 1 (Day 1) — The Hook:**
Subject line: Free report for [Company Name]
Goal: Get a reply or a call booked. Offer the free sample report. 4–5 sentences max. No pitch. Pure curiosity.

**Email 2 (Day 3) — The Problem:**
Subject line: Where do most HVAC businesses leak money?
Goal: Educate on the pain point. Name 2–3 specific financial problems common to HVAC businesses. Soft CTA.

**Email 3 (Day 7) — Social Proof:**
Subject line: What [Industry] owners find in their first report
Goal: Make it feel real. Describe (fictionally but realistically) what a business owner found in their first report and acted on. Specific numbers.

**Email 4 (Day 14) — The Direct Ask:**
Subject line: Still worth 15 minutes?
Goal: Direct ask for a call. Short. Confident. No fluff.

**Email 5 (Day 21) — The Breakup:**
Subject line: Closing your file
Goal: Final email. Create urgency. Leave the door open. 3 sentences.

**LinkedIn Message 1 (connection request):**
One sentence. Personal. Reference their business or industry.

**LinkedIn Message 2 (after connection):**
3–4 sentences. Same free sample offer. No pitch. Genuine.

Write all 7 messages. For each: subject line (if email), the full message text, and a one-line note on the goal of that message.

Save as: `outreach_sequence.md`

---

### TASK 4: Build an Excel Client Tracker
Build an actual .xlsx file to track my clients and pipeline. Tabs needed:

**Tab 1: Pipeline**
Columns: Company Name | Contact Name | Email | Phone | Industry | Source (Apollo/Referral/etc.) | Stage (Cold/Contacted/Replied/Called/Proposal Sent/Closed/Lost) | Product Interest | Est. Value | Last Contact Date | Next Action | Notes

**Tab 2: Active Clients**
Columns: Client Name | Industry | Product | Monthly Value | Start Date | Next Report Due | Status | Notes

**Tab 3: Revenue Tracker**
Columns: Month | New Clients | Churned Clients | Active Clients (auto) | MRR | One-Time Revenue | Total Revenue | MRR Target | % to Target
Include formulas. Track Jan–Dec 2026. Targets: Month 1: $2,000 | Month 2: $5,000 | Month 3: $10,000 | Month 4: $15,000

**Tab 4: Dashboard**
A summary view showing:
- Total pipeline value (sum of est. values in Pipeline tab)
- Active clients count
- Current MRR
- % to monthly target
- Next 5 follow-ups due (manually entered, clearly formatted)

Use conditional formatting: Stage column in Pipeline — color code by stage (green = Closed, yellow = Proposal Sent, blue = Called, gray = Cold). Revenue vs. target — green if >90%, yellow if 70–90%, red if <70%.

Professional styling. Navy headers (#1F2D40). Clean fonts.

Save as: `client_tracker.xlsx`

---

### TASK 5: Write a 30-Second Verbal Pitch
I need a word-for-word script for when someone asks "what do you do?" — whether on a phone call, at a networking event, or on a sales call opening.

Write 3 versions:
1. **Elevator pitch (30 seconds)** — For networking/casual. Conversational. No jargon.
2. **Cold call opener (15 seconds)** — For when they pick up the phone. Gets to the offer fast. Designed to not get hung up on.
3. **Sales call opener (60 seconds)** — For the first 60 seconds of a booked call. Sets up the problem, the solution, and what we're going to do on this call.

All three should sound like a person talking, not a pitch. Plain language. No "leverage," "synergy," "solutions," or any other business jargon. Direct and confident.

Save as: `pitch_scripts.md`

---

## KEY TECHNICAL DETAILS FOR COWORK

### Anthropic API
- Model: `claude-sonnet-4-6`
- Headers required: `x-api-key`, `anthropic-version: 2023-06-01`, `anthropic-dangerous-direct-browser-access: true`
- Max tokens: 1500 per call
- All 5 agent system prompts are embedded in the Revenue Engine dashboard HTML file

### File Output Requirements
- Word docs: Use docx-js (npm install -g docx). US Letter size (12240 x 15840 DXA). 1-inch margins. Arial font. Navy headings (#1F2D40). Professional cover page.
- Excel files: Use the xlsx skill. Color-coded. Formula-driven where possible.
- HTML: Single-file. Inline CSS. Mobile responsive. No external dependencies.
- Markdown: Clean, structured, ready to copy-paste

### Writing Style (CRITICAL — apply to everything)
- No hyphens in prose
- Contractions over formal constructions ("you'll" not "you will")
- Plain and direct — junior analyst voice
- Nothing that reads as AI generated
- No "leverage," "streamline," "synergy," "robust," "comprehensive," "cutting-edge"
- Write like a sharp 28-year-old talking to a small business owner, not like a consultant writing a proposal

---

## CONTEXT ON MY SITUATION

I am leaving for Navy OCS at the end of August 2026. That means I have approximately 90 days to build this to a point where it either (a) generates $50k or (b) can run without me, with someone else managing client delivery. Everything I build needs to be simple enough to hand off. Documentation matters.

I have strong Python skills, financial modeling background, and experience building Streamlit apps and ML pipelines. I am not a web developer but I can read and edit HTML/CSS. The priority is revenue, not engineering beauty.

The single most important thing right now is getting the first 5 paying clients. Everything else is secondary.

---

*End of briefing. Work through Tasks 1–5 in order. Save all files to the outputs directory. Flag any ambiguity in a task before skipping it.*
