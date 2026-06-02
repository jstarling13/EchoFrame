"""
agent_graph.py — LangGraph state machine that orchestrates all 4 modules.

The graph executes in this order each cycle:
  source_leads → score_leads → persist_leads
       ↓
  check_replies → handle_replies
       ↓
  run_sequence_batch
       ↓
  optimize_templates (weekly, not every cycle)

LangGraph is used here for:
  - Explicit state management across nodes
  - Conditional routing (e.g., skip optimization if not enough data)
  - Easy observability and debugging of the agent's decision path
  - Future extensibility (add nodes without touching other logic)
"""

from datetime import datetime
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END

from config import cfg
from modules.database.models import init_db, SessionLocal, LeadStage
from modules.database.crud import get_or_create_lead, update_lead_stage, log_reply
from modules.ingestion.knowledge_base import build_knowledge_base
from modules.leads.apollo_client import bulk_source_leads, RawLead
from modules.leads.google_search import source_local_leads_via_google
from modules.leads.scorer import score_and_rank, ScoredLead
from modules.outreach.reply_reader import fetch_and_classify_all, ClassifiedReply
from modules.outreach.sequence_manager import run_sequence_batch
from modules.outreach.template_optimizer import run_optimization_pass
from modules.psychology.copywriter import generate_reply_response
from modules.outreach.email_sender import send_email


# ─── Agent State ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    cycle_start: str                           # ISO timestamp
    raw_leads: list[RawLead]                   # leads fetched from sources
    scored_leads: list[ScoredLead]             # leads after scoring
    new_leads_persisted: int                   # count of net-new leads added to DB
    classified_replies: list[ClassifiedReply]  # inbound replies classified by intent
    replies_handled: int                       # positive/question replies responded to
    emails_sent: int                           # outreach touches sent this cycle
    templates_replaced: int                    # A/B test replacements this cycle
    errors: Annotated[list[str], operator.add] # accumulated error log
    run_optimization: bool                     # flag: should we run the optimizer this cycle


# ─── Node Implementations ─────────────────────────────────────────────────────

def node_source_leads(state: AgentState) -> AgentState:
    """Fetches raw leads from Apollo and Google CSE."""
    print("[Agent] Sourcing leads...")
    raw = []

    try:
        apollo_leads = bulk_source_leads(max_leads=cfg.leads_per_run)
        raw.extend(apollo_leads)
        print(f"[Agent] Apollo returned {len(apollo_leads)} leads.")
    except Exception as e:
        state["errors"].append(f"Apollo source error: {e}")

    # Google CSE as a supplementary source (lower volume, higher local specificity)
    try:
        google_results = source_local_leads_via_google()
        # Convert SearchResult to RawLead format for unified scoring
        for r in google_results:
            if r.found_email:
                from modules.leads.apollo_client import RawLead
                raw.append(RawLead(
                    first_name="",
                    last_name="",
                    email=r.found_email,
                    phone=r.found_phone or "",
                    title="Owner",  # assume owner since we targeted owner-focused queries
                    linkedin_url="",
                    company_name=r.title,
                    industry=r.industry_guess,
                    website=r.url,
                    city="",
                    state="",
                    employee_count=0,
                    has_verified_email=False,
                    has_phone=bool(r.found_phone),
                    source="google_cse",
                ))
        print(f"[Agent] Google CSE added {len(google_results)} leads.")
    except Exception as e:
        state["errors"].append(f"Google CSE source error: {e}")

    state["raw_leads"] = raw
    return state


def node_score_leads(state: AgentState) -> AgentState:
    """Scores and ranks raw leads. Filters out low-quality."""
    print(f"[Agent] Scoring {len(state['raw_leads'])} leads...")
    scored = score_and_rank(state["raw_leads"], min_score=40.0)
    print(f"[Agent] {len(scored)} leads passed quality threshold (score ≥ 40).")
    state["scored_leads"] = scored
    return state


def node_persist_leads(state: AgentState) -> AgentState:
    """Saves new leads to the database. Deduplicates by email."""
    db = SessionLocal()
    new_count = 0

    try:
        for sl in state["scored_leads"]:
            lead, created = get_or_create_lead(
                db=db,
                email=sl.raw.email,
                first_name=sl.raw.first_name,
                last_name=sl.raw.last_name,
                phone=sl.raw.phone,
                title=sl.raw.title,
                linkedin_url=sl.raw.linkedin_url,
                company_name=sl.raw.company_name,
                industry=sl.raw.industry,
                website=sl.raw.website,
                city=sl.raw.city,
                state=sl.raw.state,
                employee_count=sl.raw.employee_count,
                lead_score=sl.score,
                persona_type=sl.persona_type,
                has_verified_email=sl.raw.has_verified_email,
                has_phone=sl.raw.has_phone,
                source=sl.raw.source,
            )
            if created:
                update_lead_stage(db, lead.id, LeadStage.QUALIFIED)
                new_count += 1
    finally:
        db.close()

    print(f"[Agent] {new_count} new leads persisted.")
    state["new_leads_persisted"] = new_count
    return state


def node_check_replies(state: AgentState) -> AgentState:
    """Polls Gmail for inbound replies and classifies intent."""
    print("[Agent] Checking for replies...")
    try:
        classified = fetch_and_classify_all()
        state["classified_replies"] = classified
    except Exception as e:
        state["errors"].append(f"Reply check error: {e}")
        state["classified_replies"] = []
    return state


def node_handle_replies(state: AgentState) -> AgentState:
    """
    Processes classified replies:
      - positive/question → generate and send a response
      - negative → mark lead as NEGATIVE and halt sequence
      - auto_reply → ignore
    """
    db = SessionLocal()
    handled = 0

    try:
        from modules.database.models import Lead
        for classified in state["classified_replies"]:
            reply = classified.inbound

            # Find the lead in DB
            from sqlalchemy import select
            lead = db.query(Lead).filter(Lead.email == reply.from_email).first()
            if not lead:
                continue  # Reply from someone not in our pipeline

            # Log the reply
            log_reply(
                db=db,
                lead_id=lead.id,
                raw_body=reply.body,
                intent=classified.intent,
                confidence=classified.confidence,
                reasoning=classified.reasoning,
            )

            if classified.intent == "negative":
                update_lead_stage(db, lead.id, LeadStage.NEGATIVE)
                print(f"[Agent] Marked {reply.from_email} as NEGATIVE — halting sequence.")

            elif classified.intent in ("positive", "question"):
                update_lead_stage(db, lead.id, LeadStage.REPLIED)
                if classified.intent == "positive":
                    update_lead_stage(db, lead.id, LeadStage.POSITIVE)

                # Find the last email we sent them for context
                last_touch = max(lead.touches, key=lambda t: t.sent_at or datetime.min) if lead.touches else None
                original_body = last_touch.body_text if last_touch else ""

                try:
                    response_body = generate_reply_response(
                        original_email_body=original_body,
                        reply_body=reply.body,
                        intent=classified.intent,
                        first_name=lead.first_name or "",
                        industry=lead.industry or "",
                    )
                    if response_body:
                        send_email(
                            to_email=reply.from_email,
                            to_name=reply.from_name,
                            subject=f"Re: {reply.subject}",
                            body_text=response_body,
                        )
                        handled += 1
                except Exception as e:
                    state["errors"].append(f"Reply response error for {reply.from_email}: {e}")

            elif classified.intent == "auto_reply":
                pass  # No action needed

    finally:
        db.close()

    state["replies_handled"] = handled
    return state


def node_run_sequence(state: AgentState) -> AgentState:
    """Runs the outreach sequence batch — sends emails to leads that are due."""
    print("[Agent] Running outreach sequence batch...")
    try:
        result = run_sequence_batch(limit=cfg.leads_per_run)
        state["emails_sent"] = result.get("sent", 0)
    except Exception as e:
        state["errors"].append(f"Sequence error: {e}")
        state["emails_sent"] = 0
    return state


def node_optimize_templates(state: AgentState) -> AgentState:
    """Runs the A/B test optimizer. Only triggered when flag is set."""
    if not state.get("run_optimization"):
        state["templates_replaced"] = 0
        return state

    print("[Agent] Running template optimization pass...")
    try:
        result = run_optimization_pass()
        state["templates_replaced"] = result.get("replaced", 0)
    except Exception as e:
        state["errors"].append(f"Optimization error: {e}")
        state["templates_replaced"] = 0
    return state


def node_summarize(state: AgentState) -> AgentState:
    """Prints a human-readable cycle summary."""
    print("\n" + "=" * 60)
    print(f"[Agent] Cycle complete — {state['cycle_start']}")
    print(f"  New leads sourced:   {len(state.get('scored_leads', []))}")
    print(f"  New leads in DB:     {state.get('new_leads_persisted', 0)}")
    print(f"  Replies classified:  {len(state.get('classified_replies', []))}")
    print(f"  Replies handled:     {state.get('replies_handled', 0)}")
    print(f"  Emails sent:         {state.get('emails_sent', 0)}")
    print(f"  Templates replaced:  {state.get('templates_replaced', 0)}")
    if state.get("errors"):
        print(f"  Errors ({len(state['errors'])}):")
        for e in state["errors"]:
            print(f"    - {e}")
    print("=" * 60 + "\n")
    return state


# ─── Routing Logic ────────────────────────────────────────────────────────────

def should_optimize(state: AgentState) -> str:
    """Conditional edge: only run optimization node if flag is set."""
    return "optimize" if state.get("run_optimization") else "skip_optimize"


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("source_leads", node_source_leads)
    graph.add_node("score_leads", node_score_leads)
    graph.add_node("persist_leads", node_persist_leads)
    graph.add_node("check_replies", node_check_replies)
    graph.add_node("handle_replies", node_handle_replies)
    graph.add_node("run_sequence", node_run_sequence)
    graph.add_node("optimize_templates", node_optimize_templates)
    graph.add_node("summarize", node_summarize)

    graph.set_entry_point("source_leads")

    graph.add_edge("source_leads", "score_leads")
    graph.add_edge("score_leads", "persist_leads")
    graph.add_edge("persist_leads", "check_replies")
    graph.add_edge("check_replies", "handle_replies")
    graph.add_edge("handle_replies", "run_sequence")
    graph.add_conditional_edges(
        "run_sequence",
        should_optimize,
        {"optimize": "optimize_templates", "skip_optimize": "summarize"},
    )
    graph.add_edge("optimize_templates", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


# ─── Public Entry Point ───────────────────────────────────────────────────────

def run_agent_cycle(run_optimization: bool = False) -> AgentState:
    """
    Executes one full agent cycle. Call this from main.py or a scheduler.

    run_optimization=True: also runs the A/B test optimizer (weekly cadence recommended).
    """
    graph = build_graph()

    initial_state: AgentState = {
        "cycle_start": datetime.utcnow().isoformat(),
        "raw_leads": [],
        "scored_leads": [],
        "new_leads_persisted": 0,
        "classified_replies": [],
        "replies_handled": 0,
        "emails_sent": 0,
        "templates_replaced": 0,
        "errors": [],
        "run_optimization": run_optimization,
    }

    final_state = graph.invoke(initial_state)
    return final_state
