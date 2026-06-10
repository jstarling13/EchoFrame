# EchoFrame Autonomous Marketing Agent — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestration Layer                    │
│                      graph/agent_graph.py                           │
│                                                                     │
│  source_leads → score_leads → persist_leads                         │
│       ↓                                                             │
│  check_replies → handle_replies                                     │
│       ↓                                                             │
│  run_sequence_batch                                                 │
│       ↓                                                             │
│  optimize_templates (weekly) → summarize                            │
└─────────────────────────────────────────────────────────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
   ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐
   │ Module 1 │  │   Module 2   │  │ Module 3 │  │   Module 4   │
   │Ingestion │  │  Lead Gen    │  │  Psych   │  │  Outreach    │
   │  + KB    │  │  + Scoring   │  │  Copy    │  │  + Replies   │
   └──────────┘  └──────────────┘  └──────────┘  └──────────────┘
```

## Module 1 — Business Ingestion & Self-Training
**File:** `modules/ingestion/knowledge_base.py`

- Builds a ChromaDB vector store from 23 hardcoded EchoFrame business facts
- Optionally scrapes the live landing page and chunks the content
- Every email generation query retrieves the 5 most relevant passages
- Makes the LLM grounded in EchoFrame's actual tone, data, and value props

**Why ChromaDB:** Persistent, local, zero-dependency vector store. Industry-specific
passages surface the right context (HVAC pain points vs. restaurant pain points)
without the LLM hallucinating claims.

---

## Module 2 — Lead Generation & Scoring
**Files:** `modules/leads/apollo_client.py`, `google_search.py`, `scorer.py`

### Sources
| Source | Coverage | Quality | Use Case |
|--------|----------|---------|----------|
| Apollo.io | 250M+ contacts | High (verified emails) | Primary source |
| Google CSE | Local web | Medium (scraped) | Backup for hyper-local |

### Scoring Signals (0–100)
| Signal | Weight | Rationale |
|--------|--------|-----------|
| Verified email | 30 | No email = no outreach |
| Decision maker title | 20 | Owner/Founder bypasses gatekeepers |
| Priority industry | 15 | HVAC/plumbing/electrical convert best |
| Local geography | 15 | Columbus GA = Jacob's home turf advantage |
| Company size 2–20 | 10 | Sweet spot — too small has no budget, too big has a CFO |
| Has phone | 10 | Enables call close after email warm-up |

### Persona Assignment (drives which psych framework to use)
| Persona | Trigger | Framework |
|---------|---------|-----------|
| `risk_averse_smb_owner` | Home services, ≤10 employees | Loss aversion + authority |
| `growth_focused_operator` | Restaurant/salon | Social proof + opportunity |
| `time_starved_founder` | Solo/≤3 employees | Fogg simplicity + time-saving |

---

## Module 3 — Psychological Profiling & Copywriting
**Files:** `modules/psychology/frameworks.py`, `copywriter.py`

### Framework Architecture
Each `PsychFramework` contains:
- `email_directives` — exact instructions injected into the LLM prompt
- `forbidden_patterns` — words/phrases that break brand voice (hard-validated post-generation)
- `example_subject_patterns` / `example_opening_patterns` — style anchors

### Frameworks Implemented
**Loss Aversion + Authority** (Cialdini)
- Frame value as PREVENTING LOSS, not achieving gain
- "Leaking $1,200/month" > "Discover $1,200 in savings"
- Establishes Jacob's credentials through specific benchmark numbers, not credentials claims

**Social Proof + Opportunity** (Cialdini)
- Peer-to-peer framing: "what Columbus restaurant owners are doing"
- Competitive intelligence positioning, not financial hygiene
- Specificity makes the social proof credible (not "other businesses" — "Columbus HVAC owners")

**Time-Saving Simplicity** (Fogg Behavior Model)
- Behavior = Motivation × Ability × Prompt — removes Ability friction
- Email ≤ 6 sentences. CTA = "Reply yes" not "Book a call"
- Every step spelled out: upload CSV → get email → 5 min to read

### Sequence Psychology
```
Step 1: Primary framework (hook with core emotional lever)
Step 2: Primary framework + industry benchmark data (authority build)
Step 3: Social proof variant (cumulative trust, peer evidence)
Step 4: Direct ask (remove ambiguity)
Step 5: Breakup email (no framework — human directness)
```

### LLM Role
Claude generates ONLY the prose. Every strategic decision is made by Python:
- Which framework → `scorer.py` persona + `frameworks.py` map
- Which pain points → `INDUSTRY_PAIN_POINTS` dict in `copywriter.py`
- Which CTA → `SEQUENCE_STEP_CONTEXT` dict
- Quality validation → `_validate_email()` raises `ValueError` on forbidden patterns

---

## Module 4 — Outreach & Iteration
**Files:** `modules/outreach/email_sender.py`, `reply_reader.py`, `sequence_manager.py`, `template_optimizer.py`

### Sequence Timing
```
Step 1: Day 0  (initial send)
Step 2: Day 3
Step 3: Day 7
Step 4: Day 14
Step 5: Day 21 (breakup)
```
Send window: Tue–Thu, 7–9am (configured in `config.py`)

### Reply Classification
Gmail API polls the inbox. Claude classifies each reply:
- `positive` → generate follow-up, advance lead to POSITIVE stage
- `question` → answer directly + soft CTA, keep in pipeline
- `negative` → mark NEGATIVE, halt sequence immediately
- `auto_reply` → ignore

### A/B Test / Optimization Loop
1. After ≥20 sends, check reply rate vs. `reply_rate_floor` (4%)
2. Underperformers: Claude generates a challenger using top performers as examples
3. Underperformer is retired, challenger goes live
4. No human intervention required

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Orchestration | LangGraph | Explicit state, conditional routing, debuggable |
| LLM | Claude Sonnet 4.6 | Already integrated in EchoFrame backend |
| Vector store | ChromaDB | Local, persistent, no cloud dependency |
| Lead data | Apollo.io API | Verified emails + phones for SMB owners |
| Supplemental leads | Google Custom Search API | Hyper-local Columbus GA coverage |
| Email delivery | Resend | Already in EchoFrame stack, deliverability-first |
| Reply monitoring | Gmail API + OAuth2 | Read inbox without IMAP complexity |
| Database | SQLite → PostgreSQL | Local dev; swap URL for prod scale |
| Scheduling | `schedule` library | Lightweight; swap for APScheduler or cron in prod |

---

## File Structure

```
echoframe-agent/
├── main.py                          # CLI entry point (run/schedule/status/dry-run)
├── config.py                        # All configuration, loaded from .env
├── requirements.txt
├── .env.example                     # Template — copy to .env, fill in keys
│
├── modules/
│   ├── ingestion/
│   │   └── knowledge_base.py        # ChromaDB vector store + EchoFrame facts
│   │
│   ├── leads/
│   │   ├── apollo_client.py         # Apollo.io API wrapper + pagination
│   │   ├── google_search.py         # Google CSE + website contact scraping
│   │   └── scorer.py                # Lead scoring (0–100) + persona assignment
│   │
│   ├── psychology/
│   │   ├── frameworks.py            # Cialdini/Fogg framework definitions
│   │   └── copywriter.py            # LLM-powered email generation + validation
│   │
│   ├── outreach/
│   │   ├── email_sender.py          # Resend API wrapper
│   │   ├── reply_reader.py          # Gmail API + intent classifier
│   │   ├── sequence_manager.py      # 5-step sequence timing + batch runner
│   │   └── template_optimizer.py   # A/B test loop + challenger generation
│   │
│   └── database/
│       ├── models.py                # SQLAlchemy ORM (Lead, Touch, Reply, Template)
│       └── crud.py                  # All DB operations
│
├── graph/
│   └── agent_graph.py               # LangGraph state machine connecting all modules
│
└── data/
    ├── knowledge_base/              # ChromaDB persistent store (auto-created)
    ├── gmail_credentials.json       # OAuth2 creds (download from GCP, gitignored)
    └── echoframe_agent.db           # SQLite database (auto-created)
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env
# Edit .env with your API keys

# 3. Build the knowledge base
python main.py build-kb

# 4. Test email generation without sending
python main.py dry-run

# 5. Run one full cycle
python main.py run

# 6. Check pipeline status
python main.py status

# 7. Run on daily schedule
python main.py schedule
```

---

## Gmail Setup (one-time)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → Enable **Gmail API**
3. Create credentials → **OAuth 2.0 Client ID** → Desktop app
4. Download `credentials.json` → save to `data/gmail_credentials.json`
5. First `python main.py run` will open a browser for OAuth consent
6. Token is saved to `data/gmail_token.json` — subsequent runs are headless

---

## Scaling Notes

- **Volume:** The agent is capped at `leads_per_run=50` and `max_concurrent_sequences=200` in config.
  Increase when Apollo rate limits allow and Resend sending reputation is established.
- **Database:** Swap `DATABASE_URL` to PostgreSQL when you hit 10k+ leads.
- **Scheduling:** Replace `schedule` library with APScheduler or a cron job for production reliability.
- **Monitoring:** Add Sentry or Datadog for error tracking — the `errors` field in AgentState
  captures all failures per cycle.
