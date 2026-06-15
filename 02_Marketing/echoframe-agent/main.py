"""
main.py — EchoFrame Autonomous Marketing Agent

Entry point for all agent operations:
  - `python main.py run`            → run one full agent cycle
  - `python main.py run --optimize` → run cycle + A/B test optimization
  - `python main.py build-kb`       → rebuild the knowledge base
  - `python main.py dry-run`        → generate emails but don't send
  - `python main.py schedule`       → run on a schedule (every weekday 7am)
  - `python main.py status`         → print pipeline stats

All four modules execute in sequence: ingest → lead gen → psych copy → outreach.
"""

import argparse
import sys
from datetime import datetime

import schedule
import time

from config import cfg
from modules.database.models import init_db
from modules.ingestion.knowledge_base import build_knowledge_base
from graph.agent_graph import run_agent_cycle
from modules.outreach.sequence_manager import run_sequence_batch


def cmd_build_kb(args):
    print("[KB] Building EchoFrame knowledge base...")
    extra_urls = []
    # Uncomment to also scrape the live landing page:
    # extra_urls = ["https://echoframe.io"]
    build_knowledge_base(extra_urls=extra_urls)
    print("[KB] Done.")


def cmd_run(args):
    run_optimization = getattr(args, "optimize", False)
    print(f"[Main] Starting agent cycle — optimize={run_optimization}")
    final_state = run_agent_cycle(run_optimization=run_optimization)
    if final_state["errors"]:
        sys.exit(1)


def cmd_dry_run(args):
    """
    Sources leads from Apollo, scores them, then generates emails without sending.
    Gives you a full preview of what the agent would send on its first real cycle.
    """
    print("[Main] DRY RUN — sourcing leads and generating emails. Nothing will be sent.\n")

    from modules.leads.apollo_client import bulk_source_leads
    from modules.leads.scorer import score_and_rank
    from modules.psychology.copywriter import generate_email

    # ── Check Hunter credits first ────────────────────────────────────────────
    from modules.leads.hunter_client import check_credits
    credits = check_credits()
    if credits:
        print(f"[Hunter.io] Searches available this month: {credits.get('searches_available', '?')}")
        print(f"[Hunter.io] Searches used: {credits.get('searches_used', '?')}\n")

    print("[Dry Run] Pulling leads from Apollo...")
    raw = bulk_source_leads(max_leads=10)

    if not raw:
        print("[Dry Run] Apollo returned no leads (free plan restriction or no credits).")
        print("[Dry Run] Using Columbus GA mock leads to demonstrate the copywriting engine.\n")
        from modules.leads.apollo_client import RawLead
        raw = [
            RawLead("Mike", "Hargrove", "mhargrove@hvaccolumbus.com", "706-555-0182",
                    "Owner", "", "Hargrove Heating & Cooling", "HVAC",
                    "hvaccolumbus.com", "Columbus", "GA", 8, True, True),
            RawLead("Sandra", "Petit", "sandra@forkandfirekitchen.com", "706-555-0347",
                    "Owner", "", "Fork & Fire Kitchen", "Restaurant",
                    "forkandfire.com", "Columbus", "GA", 14, True, True),
            RawLead("Derrick", "Owens", "dowens@owensplumbing.net", "334-555-0291",
                    "Founder", "", "Owens Plumbing Co", "Plumbing",
                    "owensplumbing.net", "Phenix City", "AL", 5, True, False),
            RawLead("Tanya", "Rhodes", "tanya@elevatestudio.com", "706-555-0419",
                    "CEO", "", "Elevate Salon & Studio", "Salon",
                    "elevatestudio.com", "Columbus", "GA", 6, True, True),
            RawLead("James", "Whitfield", "jwhitfield@whitfieldelectric.com", "706-555-0533",
                    "Owner", "", "Whitfield Electric", "Electrical",
                    "whitfieldelectric.com", "Auburn", "AL", 3, False, True),
        ]

    scored = score_and_rank(raw, min_score=40.0)
    print(f"[Dry Run] {len(raw)} leads fetched → {len(scored)} passed scoring (≥40).\n")

    if not scored:
        print("[Dry Run] All leads scored below threshold. Try lowering min_score or check Apollo filters.")
        return

    print("=" * 65)
    for i, sl in enumerate(scored[:5], 1):
        lead = sl.raw
        print(f"\n{'─'*65}")
        print(f"Lead {i}: {lead.first_name} {lead.last_name} | {lead.title} @ {lead.company_name}")
        print(f"         {lead.industry} | {lead.city}, {lead.state} | Score: {sl.score:.0f}/100")
        print(f"         Persona: {sl.persona_type} | Signals: {list(sl.signals.keys())}")
        print()

        try:
            email = generate_email(
                first_name=lead.first_name or "there",
                company_name=lead.company_name or "your business",
                industry=lead.industry or "small business",
                city=lead.city or "Columbus",
                employee_count=lead.employee_count or 5,
                persona_type=sl.persona_type,
                sequence_step=1,
            )
            print(f"SUBJECT: {email.subject}")
            print(f"FRAMEWORK: {email.framework_used}")
            print(f"\nBODY:\n{email.body}")
        except Exception as e:
            print(f"[ERROR] Email generation failed: {e}")

    print(f"\n{'='*65}")
    print(f"[Dry Run] Complete. Run `python main.py run` to go live.")


def cmd_schedule(args):
    """Runs the agent on a daily schedule (Mon–Fri at 7am)."""
    print("[Main] Scheduling agent to run Mon–Fri at 07:00...")

    def job():
        # Run optimization every Monday
        today = datetime.now().weekday()
        run_optimization = (today == 0)
        print(f"\n[Scheduler] Firing agent cycle (optimize={run_optimization})")
        run_agent_cycle(run_optimization=run_optimization)

    schedule.every().monday.at("07:00").do(job)
    schedule.every().tuesday.at("07:00").do(job)
    schedule.every().wednesday.at("07:00").do(job)
    schedule.every().thursday.at("07:00").do(job)
    schedule.every().friday.at("07:00").do(job)

    print("[Scheduler] Agent scheduled. Running loop — press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(60)


def cmd_prospect(args):
    """
    Full local prospecting pipeline without Apollo:
      Google search → real business domains → Hunter email lookup → score → save to DB

    Uses Hunter credits efficiently — only searches domains that Google confirmed
    are real local businesses with a web presence.
    """
    from modules.leads.google_maps import bulk_search_local_businesses
    from modules.leads.hunter_client import check_credits, enrich_domains_with_hunter
    from modules.leads.scorer import score_and_rank
    from modules.database.models import SessionLocal, init_db
    from modules.database.crud import get_or_create_lead, update_lead_stage
    from modules.database.models import LeadStage

    # Check credits before burning them
    credits = check_credits()
    available = credits.get("searches_available", 0)
    print(f"\n[Prospect] Hunter credits available: {available}")

    if available < 5:
        print("[Prospect] Less than 5 Hunter credits remaining — aborting to preserve credits.")
        return

    # How many domains to search (leave 5 credits as buffer)
    max_domains = min(available - 5, getattr(args, "limit", 40))
    print(f"[Prospect] Will search up to {max_domains} domains.\n")

    # ── Manual domain list bypasses the scraper entirely ─────────────────────
    manual_domains_arg = getattr(args, "domains", None)
    if manual_domains_arg:
        # Format: "domain1.com:Company Name:Industry,domain2.com:Company 2:Industry"
        domain_list = []
        for entry in manual_domains_arg.split(","):
            parts = entry.strip().split(":")
            domain_list.append({
                "domain": parts[0].strip(),
                "company_name": parts[1].strip() if len(parts) > 1 else "",
                "industry": parts[2].strip() if len(parts) > 2 else "HVAC",
                "city": "Columbus",
                "state": "GA",
            })
        print(f"[Prospect] Using {len(domain_list)} manually provided domains.\n")
    else:
        # Step 1: Google/DDG → real local business domains
        industries = getattr(args, "industries", None)
        businesses = bulk_search_local_businesses(
            industries=industries.split(",") if industries else None,
            results_per_query=8,
        )

        if not businesses:
            print("[Prospect] Web scraper returned 0 domains (likely rate-limited).")
            print("[Prospect] Pass real domains directly with --domains flag:")
            print('  Example: python main.py prospect --domains "reliableair.com:Reliable Heating & Air:HVAC,jonesplumbing.com:Jones Plumbing:Plumbing"')
            return

        domain_list = [
            {"domain": b.domain, "company_name": b.name,
             "industry": b.industry, "city": b.city, "state": b.state}
            for b in businesses[:max_domains]
        ]

    raw_leads = enrich_domains_with_hunter(domain_list)
    print(f"\n[Prospect] Hunter returned {len(raw_leads)} contacts from {len(domain_list)} domains.")

    if not raw_leads:
        print("[Prospect] No emails found. Try different industries or locations.")
        return

    # Step 3: Score and filter
    scored = score_and_rank(raw_leads, min_score=30.0)  # lower threshold since Hunter leads have no phone
    print(f"[Prospect] {len(scored)} leads passed scoring.\n")

    # Step 4: Save to DB
    init_db()
    db = SessionLocal()
    new_count = 0
    try:
        for sl in scored:
            lead, created = get_or_create_lead(
                db=db,
                email=sl.raw.email,
                first_name=sl.raw.first_name,
                last_name=sl.raw.last_name,
                title=sl.raw.title,
                company_name=sl.raw.company_name,
                industry=sl.raw.industry,
                website=sl.raw.website,
                city=sl.raw.city,
                state=sl.raw.state,
                lead_score=sl.score,
                persona_type=sl.persona_type,
                has_verified_email=sl.raw.has_verified_email,
                source="hunter",
            )
            if created:
                update_lead_stage(db, lead.id, LeadStage.QUALIFIED)
                new_count += 1
                print(f"  + {sl.raw.first_name} {sl.raw.last_name} | {sl.raw.company_name} | {sl.raw.email} (score: {sl.score:.0f})")
    finally:
        db.close()

    remaining = check_credits().get("searches_available", "?")
    print(f"\n[Prospect] Done. {new_count} new leads saved to DB.")
    print(f"[Prospect] Hunter credits remaining: {remaining}")
    print(f"\nRun `python main.py dry-run` to preview emails, or `python main.py run` to send.")


def cmd_hunter_test(args):
    """Shows Hunter.io credit balance and tests a single domain lookup."""
    from modules.leads.hunter_client import check_credits, domain_search, _extract_best_contact

    credits = check_credits()
    if credits:
        print(f"\nHunter.io Account Status:")
        print(f"  Searches:      {credits.get('searches_used', 0)} used / {credits.get('searches_available', 0)} remaining")
        print(f"  Verifications: {credits.get('verifications_used', 0)} used / {credits.get('verifications_available', 0)} remaining")
    else:
        print("Could not reach Hunter.io — check your HUNTER_API_KEY in .env")
        return

    # Test with a real Columbus GA business domain (costs 1 search credit)
    test_domain = "hargroveheatingandcooling.com"
    print(f"\nTest search on {test_domain} (costs 1 credit)...")
    result = domain_search(test_domain, "Hargrove Heating & Cooling")
    if result:
        lead = _extract_best_contact(result, industry="HVAC", city="Columbus", state="GA")
        if lead:
            print(f"  Found: {lead.first_name} {lead.last_name} | {lead.title} | {lead.email}")
        else:
            print(f"  Domain found but no owner-level contact identified.")
            print(f"  Raw emails: {[e.get('value') for e in result.found_emails]}")
    else:
        print(f"  No results for {test_domain}")


def cmd_status(args):
    """Prints pipeline statistics from the database."""
    from modules.database.models import SessionLocal, Lead, LeadStage, OutreachTouch, Reply
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total = db.query(func.count(Lead.id)).scalar()
        by_stage = (
            db.query(Lead.stage, func.count(Lead.id))
            .group_by(Lead.stage)
            .all()
        )
        total_sends = db.query(func.count(OutreachTouch.id)).scalar()
        total_replies = db.query(func.count(Reply.id)).scalar()
        positive_replies = db.query(func.count(Reply.id)).filter(Reply.intent == "positive").scalar()

        print("\n" + "=" * 50)
        print("EchoFrame Agent — Pipeline Status")
        print("=" * 50)
        print(f"Total leads:      {total}")
        print(f"\nBy stage:")
        for stage, count in sorted(by_stage, key=lambda x: x[1], reverse=True):
            print(f"  {str(stage.value):<20} {count}")
        print(f"\nTotal touches:    {total_sends}")
        print(f"Total replies:    {total_replies}")
        print(f"Positive replies: {positive_replies}")
        if total_sends > 0:
            print(f"Overall reply rate: {total_replies / total_sends:.1%}")
            print(f"Positive rate:      {positive_replies / total_sends:.1%}")
        print("=" * 50 + "\n")
    finally:
        db.close()


def main():
    # Initialize DB on every startup
    init_db()

    parser = argparse.ArgumentParser(description="EchoFrame Autonomous Marketing Agent")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run", help="Run one agent cycle")
    run_parser.add_argument("--optimize", action="store_true",
                            help="Also run template optimization pass")

    # build-kb
    subparsers.add_parser("build-kb", help="Rebuild the knowledge base")

    # dry-run
    subparsers.add_parser("dry-run", help="Generate emails without sending")

    # schedule
    subparsers.add_parser("schedule", help="Run on daily schedule")

    # status
    subparsers.add_parser("status", help="Print pipeline statistics")

    # hunter-test
    subparsers.add_parser("hunter-test", help="Check Hunter.io credits and test a domain lookup")

    # prospect
    prospect_parser = subparsers.add_parser("prospect", help="Google → Hunter pipeline: find and save real local leads")
    prospect_parser.add_argument("--limit", type=int, default=40, help="Max Hunter searches to use (default 40)")
    prospect_parser.add_argument("--industries", type=str, help="Comma-separated industries e.g. 'HVAC,Plumbing'")
    prospect_parser.add_argument("--domains", type=str, help="Manually specify domains: 'site.com:Company:Industry,...'")

    args = parser.parse_args()

    dispatch = {
        "run": cmd_run,
        "build-kb": cmd_build_kb,
        "dry-run": cmd_dry_run,
        "schedule": cmd_schedule,
        "status": cmd_status,
        "hunter-test": cmd_hunter_test,
        "prospect": cmd_prospect,
    }

    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
