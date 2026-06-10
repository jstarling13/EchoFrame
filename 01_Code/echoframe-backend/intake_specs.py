"""
EchoFrame - per-product intake (Step 2 secure-upload) page specs.
-----------------------------------------------------------------------------
Each product gets a customer-facing upload page that instructs the buyer to
provide exactly the data THAT product's report needs (Drive Pay = repair-order
payment outcomes, not a P&L). All single-file pages share templates/intake.html.

Revenue Suite needs three CSVs at once, so it has its own page
(templates/intake_revenue_suite.html) and its own backend route. It is NOT in
INTAKE_SPECS because it does not fit the single-file template.

Preview one page:    python intake_specs.py drive-pay
Preview every page:  python intake_specs.py all
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
PREVIEW_DIR = BASE_DIR / "reports"

# Common reusable fields ---------------------------------------------------------
F_BUSINESS = {"type": "text", "name": "business", "label": "Business name",
              "placeholder": "e.g. Cross Creek Auto Repair", "required": True}
F_MONTH = {"type": "text", "name": "month", "label": "Reporting month",
           "placeholder": "e.g. June 2026", "required": True}
F_CITY = {"type": "text", "name": "location", "label": "City & State",
          "placeholder": "e.g. Columbus, GA", "required": True}
F_ROLE = {"type": "text", "name": "role", "label": "Role you're hiring for",
          "placeholder": "e.g. Diesel Technician", "required": True}
F_INDUSTRY = {"type": "text", "name": "industry", "label": "Industry",
              "placeholder": "e.g. HVAC, Salon, Restaurant", "required": True}
F_PERIOD = {"type": "text", "name": "month", "label": "Reporting period",
            "placeholder": "e.g. Week of June 1-7, 2026", "required": True}


INTAKE_SPECS: dict[str, dict] = {
    "drive-pay": {
        "report_name": "Drive Pay report",
        "headline": "Connect your pickup payments.",
        "sub": "Export your closed repair orders and their payment outcomes, then drop the file "
               "below. Your Drive Pay report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per closed repair order, with:",
        "requirements": [
            "Date & time the repair order closed",
            "Customer name",
            "Vehicle - year, make & model",
            "Invoice total ($)",
            "Payment outcome - paid at pickup, paid later, or unpaid",
            "Time from pay-link sent to payment cleared (if available)",
        ],
        "where": "Most shop-management systems (Tekmetric, Shop-Ware, Mitchell 1, etc.) can export "
                 "closed repair orders with payment status to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your repair-order export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Drive Pay report",
    },
    "clarity": {
        "report_name": "Monthly Clarity Report",
        "headline": "Upload your monthly P&L.",
        "sub": "Drop your profit & loss statement below. Your Monthly Clarity Report will be "
               "in your inbox within minutes.",
        "fields": [F_INDUSTRY, F_CITY],
        "requirements_title": "Your file should be a monthly P&L that includes:",
        "requirements": [
            "Total revenue / sales for the month",
            "Each expense line item with its amount",
            "Prior-month figures too, if you have them (sharpens the trends)",
        ],
        "where": "Your accounting tool (QuickBooks, Xero, Wave) can export a Profit & Loss "
                 "statement to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your P&L statement here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Clarity Report",
    },
    "auto-ledger": {
        "report_name": "Auto Ledger report",
        "headline": "Upload this month's transactions.",
        "sub": "Export your bank and credit-card activity for the month, then drop the file "
               "below. Your Auto Ledger report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per transaction, with:",
        "requirements": [
            "Date of each transaction",
            "Description / payee",
            "Amount - signed (deposits positive, expenses negative)",
            "Account it came from (checking, card, etc.)",
            "Optional: your accounting revenue & net-income totals for the month",
        ],
        "where": "Your bank and credit-card sites export transactions to CSV; most accounting "
                 "tools do too.",
        "file_accept": ".csv",
        "file_label": "Drop your transaction export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Auto Ledger report",
    },
    "rate-watch": {
        "report_name": "Rate Watch report",
        "headline": "Upload your vendor & recurring bills.",
        "sub": "List the vendors and recurring bills you want checked, then drop the file "
               "below. Your Rate Watch report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per vendor or recurring bill, with:",
        "requirements": [
            "Vendor name",
            "Category (e.g. card processing, software, insurance)",
            "Current rate or contract amount ($)",
            "Billing basis (monthly, % of volume, per unit, etc.)",
            "Renewal or contract-end date",
        ],
        "where": "Pull these from your bills, statements, and vendor contracts into a simple "
                 "spreadsheet, then export to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your vendor list here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Rate Watch report",
    },
    "shift-lens": {
        "report_name": "Shift Lens report",
        "headline": "Upload your sales & labor by shift.",
        "sub": "Combine your POS sales and labor hours per shift, then drop the file below. "
               "Your Shift Lens report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per shift, with:",
        "requirements": [
            "Day & time block of the shift",
            "Revenue earned that shift",
            "Labor hours worked",
            "Labor / wage cost for the shift",
        ],
        "where": "Your POS exports sales by shift; your scheduling or timeclock tool exports "
                 "hours & labor cost. Combine them into one CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your shift data here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Shift Lens report",
    },
    "quote-revive": {
        "report_name": "Quote Revive report",
        "headline": "Upload your open quotes.",
        "sub": "Export the quotes still sitting open, then drop the file below. Your Quote "
               "Revive report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per open quote, with:",
        "requirements": [
            "Quote / estimate ID",
            "Job description",
            "Quote value ($)",
            "Date the quote was sent",
            "Number of follow-ups already sent",
            "Current status (open, won, lost)",
        ],
        "where": "Your quoting or CRM tool (Jobber, ServiceTitan, Housecall Pro, etc.) can "
                 "export open estimates to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your open-quotes export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Quote Revive report",
    },
    "clear-ledger": {
        "report_name": "Clear Ledger report",
        "headline": "Upload your open invoices.",
        "sub": "Export your A/R aging or open-invoices report, then drop the file below. Your "
               "Clear Ledger report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per open invoice, with:",
        "requirements": [
            "Customer name",
            "Invoice number",
            "Amount owed ($)",
            "Due date (or days overdue)",
            "Optional: total collected this month & average days-to-pay",
        ],
        "where": "QuickBooks, Xero, or FreshBooks can export an A/R aging or open-invoices "
                 "report to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your A/R aging export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Clear Ledger report",
    },
    "permit-watch": {
        "report_name": "Permit Watch report",
        "headline": "Upload your licenses & fleet records.",
        "sub": "List the licenses, permits, and fleet items you want tracked, then drop the "
               "file below. Your Permit Watch report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per license, permit, or fleet item, with:",
        "requirements": [
            "What the item is (license, tag, inspection, insurance, etc.)",
            "Entity or vehicle it belongs to",
            "Expiration / renewal date",
        ],
        "where": "List your business licenses, vehicle registrations, certifications, and "
                 "insurance renewals in a spreadsheet, then export to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your license & fleet list here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Permit Watch report",
    },
    "bay-coach": {
        "report_name": "Bay Coach report",
        "headline": "Upload your vehicle service history.",
        "sub": "Export your per-vehicle service history and odometer readings, then drop the "
               "file below. Your Bay Coach report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include, per vehicle:",
        "requirements": [
            "Vehicle - year, make & model",
            "Current mileage / odometer",
            "Past services with their dates",
            "Your shop's pricing for the services you offer",
        ],
        "where": "Your shop-management system / DMS (Tekmetric, Mitchell 1, Shop-Ware, etc.) "
                 "exports vehicle service history to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your service-history export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Bay Coach report",
    },
    "call-catch": {
        "report_name": "Call Catch report",
        "headline": "Export your missed-call log.",
        "sub": "Export your missed calls and the auto-texts that went out, then drop the file "
               "below. Your Call Catch report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include one row per missed call, with:",
        "requirements": [
            "Time of the call",
            "Caller (name or number)",
            "Auto-text that was sent back",
            "Whether the caller replied",
            "Outcome - booked job & its value ($), if any",
        ],
        "where": "Most VoIP / business-phone systems (OpenPhone, RingCentral, Dialpad) export "
                 "call logs with text history to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your missed-call log here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Call Catch report",
    },
    "call-router": {
        "report_name": "Call Router report",
        "headline": "Export your inbound-call log.",
        "sub": "Export your inbound calls with how each was routed and what it booked, then "
               "drop the file below. Your Call Router report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_PERIOD],
        "requirements_title": "Your file should include one row per inbound call, with:",
        "requirements": [
            "Time of the call",
            "What the caller needed",
            "Urgency (emergency, routine, etc.)",
            "Who the call was routed to",
            "Booked outcome & value ($), if any",
        ],
        "where": "Your business-phone system exports inbound-call logs to CSV; add routing & "
                 "outcome notes if your system tracks them.",
        "file_accept": ".csv",
        "file_label": "Drop your inbound-call log here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Call Router report",
    },
    "rival-scan": {
        "report_name": "Rival Scan report",
        "headline": "Tell us who to watch.",
        "sub": "List the competitors you want watched and the one price you want compared, "
               "then drop the file below. Your Rival Scan report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_MONTH],
        "requirements_title": "Your file should include:",
        "requirements": [
            "Your business and the one key item you want compared (e.g. Lg 1-topping pizza)",
            "Your own price for that item",
            "3-5 competitors you want watched",
            "For each competitor: their price for that same item",
            "Any promos or review highlights you already know (optional)",
        ],
        "where": "List your competitors and their advertised prices (from their menus or sites) "
                 "in a spreadsheet alongside your own price, then export to CSV.",
        "file_accept": ".csv",
        "file_label": "Drop your competitor list here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Rival Scan report",
    },
    "crew-hire": {
        "report_name": "Crew Hire report",
        "headline": "Upload your applicants.",
        "sub": "Export the applicants for your open role, then drop the file below. Your Crew "
               "Hire report will be in your inbox within minutes.",
        "fields": [F_BUSINESS, F_ROLE],
        "requirements_title": "Your file should include one row per applicant, with:",
        "requirements": [
            "The role you're hiring for and any must-have requirements",
            "Applicant name",
            "Their screening scores / how they stack up on your must-haves",
            "Current status (new, screened, interviewing, etc.)",
        ],
        "where": "Export applicants from your job board or ATS (Indeed, ZipRecruiter, etc.) to "
                 "CSV, with any screening notes you've added.",
        "file_accept": ".csv",
        "file_label": "Drop your applicant export here",
        "file_hint": "or click to browse  -  .csv files only",
        "button": "Generate my Crew Hire report",
    },
}


def _chunk_rows(fields, per_row=2):
    return [fields[i:i + per_row] for i in range(0, len(fields), per_row)]


def build_context(slug: str, tier: str = "", tier_label: str = "") -> dict:
    spec = INTAKE_SPECS[slug]
    return {
        "slug": slug,
        "tier": tier,
        "tier_label": tier_label,
        "headline": spec["headline"],
        "headline_plain": spec["headline"].rstrip("."),
        "sub": spec["sub"],
        "report_name": spec["report_name"],
        "field_rows": _chunk_rows(spec["fields"]),
        "requirements_title": spec["requirements_title"],
        "requirements": spec["requirements"],
        "where": spec.get("where", ""),
        "file_accept": spec["file_accept"],
        "file_label": spec["file_label"],
        "file_hint": spec["file_hint"],
        "button": spec["button"],
    }


def render_intake(slug: str, tier: str = "", tier_label: str = "") -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)),
                      autoescape=select_autoescape(["html"]))
    html = env.get_template("intake.html").render(**build_context(slug, tier, tier_label))
    PREVIEW_DIR.mkdir(exist_ok=True)
    out = PREVIEW_DIR / f"intake_{slug.replace('-', '_')}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[Intake] {slug} -> {out}")
    return str(out)


def render_all() -> list[str]:
    return [render_intake(slug) for slug in INTAKE_SPECS]


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        render_all()
    else:
        render_intake(target)
