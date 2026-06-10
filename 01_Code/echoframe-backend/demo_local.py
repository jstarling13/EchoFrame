"""
EchoFrame Clarity Report — fully-offline local demo
─────────────────────────────────────────────────────────────────────────────
Generates a REAL, branded 4-page .docx Clarity Report from a sample CSV, with
EVERY external service mocked. No network calls are made:

  • Anthropic (Claude)  → mocked: _generate_narrative returns canned prose
  • Resend (email)      → mocked: _send_report_email is a no-op (nothing is sent)
  • Stripe              → not involved (this bypasses the paid web flow entirely)

This proves the math + document pipeline end-to-end without any API keys, money,
or email. Output lands in   echoframe-backend/demo_output/.

Run:
    python demo_local.py

The only third-party libraries needed are the analysis/doc ones (pandas, python-docx,
matplotlib) — already in requirements.txt. anthropic/resend are imported by engine.py
at module load but are never *called* here.
"""

import os
import sys
from pathlib import Path

# Placeholder env so importing engine.py is friction-free (engine doesn't call out
# at import time; these are belt-and-suspenders and are never used for real calls).
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-demo-not-used")
os.environ.setdefault("RESEND_API_KEY", "re_demo-not-used")

import engine  # noqa: E402

BASE_DIR   = Path(__file__).resolve().parent
DEMO_DIR   = BASE_DIR / "demo_output"
DEMO_DIR.mkdir(exist_ok=True)

DEMO_EMAIL = "demo@echoframe.local"

# Sample CSV — same schema the real product ingests (HVAC field-service business).
SAMPLE_CSV = """_Business Name,Reliable Heating & Air,
_Owner Name,Shane,
_Industry,HVAC,
_Location,Columbus GA,
_Employees,8,
_Month,May 2026,
_Context,Spring AC tune-up season. Strong revenue but two equipment purchases and a van repair hit hard. Payroll rose after hiring a second seasonal tech.,
Revenue,52000,44000
Labor Cost,18720,14080
Parts & Materials,9360,8800
Vehicle & Fuel,3120,2200
Equipment,4160,1320
Rent,1560,1560
Marketing,780,880
Utilities,624,528
Misc,1040,880
"""


def _canned_prose(*_args, **_kwargs) -> dict:
    """Stand-in for _generate_narrative — returns prose covering every field the
    document builder reads, so the demo .docx is fully populated without Claude."""
    return {
        "executive_summary": (
            "$52,000 in revenue this month, up 18.2% over the prior month, with net income of "
            "$12,636 (24.3% margin). The business is simultaneously over-invested in labor and "
            "under-invested in marketing: a second seasonal tech lifted payroll above the sector "
            "median while marketing slipped below it. If labor scheduling is not aligned to "
            "demand over the next quarter, the seasonal margin gain erodes and growth spend stays "
            "starved heading into the slower fall season."
        ),
        "revenue_analysis": (
            "Revenue of $52,000 reflects peak spring tune-up demand for Reliable Heating & Air. "
            "The 18.2% lift is seasonal and should not be annualized as a run rate."
        ),
        "revenue_bullets_insight": [
            "Spring AC demand drove the strongest month of the trailing period.",
            "Net margin of 24.3% is healthy but inflated by one-time equipment timing.",
            "Labor scaled faster than revenue, compressing the underlying operating margin.",
        ],
        "revenue_bullets_next": [
            "Hold labor as a percent of revenue flat as demand normalizes next month.",
            "Protect a marketing floor to keep the fall pipeline from thinning.",
        ],
        "leak_1_analysis": (
            "Labor cost of $18,720 is 36.0% of revenue, roughly $520 above the 35% sector median. "
            "The second seasonal tech raised loaded payroll faster than billable hours grew. Pull "
            "the May payroll register and reconcile scheduled hours against completed work orders."
        ),
        "leak_2_analysis": (
            "Equipment spend of $4,160 (8.0% of revenue) is well above a normalized run rate. The "
            "gap is driven by two one-time purchases this month. Confirm these are capitalized, not "
            "expensed, before reading them as recurring overhead."
        ),
        "leak_3_analysis": (
            "Vehicle & fuel of $3,120 (6.0% of revenue) sits slightly above the field-service "
            "median. A van repair inflated the month. Log the repair separately from routine fuel "
            "to see the true recurring vehicle cost."
        ),
        "leak_4_analysis": (
            "Parts & materials of $9,360 (18.0% of revenue) is within the expected band for HVAC. "
            "Track it as a watch metric. Verify markup on parts is holding at target on each ticket."
        ),
        "leak_5_analysis": (
            "Misc of $1,040 (2.0% of revenue) is unremarkable this month. Keep an itemized log so "
            "recurring costs do not accumulate unexamined inside a catch-all line."
        ),
        "cash_flow_analysis": (
            "Net income of $12,636 implies a strong cash month, though two equipment purchases "
            "consumed part of it. Cash position should improve as seasonal receivables clear."
        ),
        "cash_flow_bullets": [
            "Operating cash is positive and supported by a 24.3% net margin.",
            "One-time equipment outlays reduced free cash this month only.",
            "Set aside a reserve for the slower fall season before discretionary spend.",
        ],
        "projection_base_case": "With no changes, margins normalize to roughly 18-20% as seasonal demand cools.",
        "projection_quick_wins": "Tightening labor scheduling alone holds net margin near 22% into next month.",
        "projection_full_plan": "Aligning labor to demand and restoring marketing supports both margin and fall pipeline.",
        "one_thing_why": (
            "Labor is the highest-leverage lever because it is the largest controllable cost and it "
            "scaled ahead of revenue. Aligning it to demand protects the seasonal margin gain."
        ),
        "one_thing_risk": (
            "This assumes scheduling can flex without hurting response times; evaluate job completion "
            "speed before trimming any customer-facing shifts."
        ),
        "one_thing_steps": [
            "Pull the May payroll register and list every tech, role, scheduled hours, and loaded cost.",
            "Match scheduled hours against completed work orders to find idle or overlapping shifts.",
            "Draft a demand-aligned schedule for next month using last year's June ticket volume.",
            "Confirm response-time coverage in the new schedule before implementing it.",
        ],
        "one_thing_impact": (
            "Full recovery of the labor overage returns about $520/mo to net income based on the "
            "current month run rate."
        ),
        "next_step_this_week": "Pull the payroll register and flag any shift without matching billable work.",
        "next_step_this_month": "Build a demand-aligned schedule for next month and review it against coverage needs.",
        "next_step_30_days": "Restore marketing to a defined monthly floor to protect the fall pipeline.",
        "next_step_60_days": "Reconcile equipment purchases as capital items and update the expense baseline.",
        "next_step_90_days": "Review trailing-quarter labor percent against target and adjust seasonal hiring.",
        "closing_sentence": (
            "Next month's report will track labor cost %, utility spend, and marketing allocation "
            "against the targets set here."
        ),
    }


def main() -> int:
    # Redirect engine I/O to the demo folder so we never touch real uploads/reports.
    engine.UPLOADS_DIR = DEMO_DIR
    engine.REPORTS_DIR = DEMO_DIR

    # Write the sample CSV under the email the engine will look up.
    safe = engine._safe_email(DEMO_EMAIL)
    (DEMO_DIR / f"{safe}.csv").write_text(SAMPLE_CSV, encoding="utf-8")

    # Mock the two external-service steps.
    sent = {"called": False}

    def _no_send(*_a, **_k):
        sent["called"] = True
        print("[demo] _send_report_email mocked — NO email sent.")

    engine._generate_narrative = _canned_prose
    engine._send_report_email = _no_send

    print("[demo] Generating Clarity Report (all external calls mocked)...")
    path = engine.generate_clarity_report(
        customer_email=DEMO_EMAIL,
        customer_name="Shane",
        industry="HVAC",
        location="Columbus GA",
    )

    if not path or not Path(path).exists():
        print("[demo] FAILED — no report file was produced.", file=sys.stderr)
        return 1

    size_kb = Path(path).stat().st_size / 1024
    print(f"[demo] SUCCESS — report written: {path}  ({size_kb:,.1f} KB)")
    print(f"[demo] Email send was mocked (called={sent['called']}); nothing left the machine.")
    print(f"[demo] Open the .docx in '{DEMO_DIR}' to view the 4-page report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
