"""
EchoFrame — Auto Ledger report engine
─────────────────────────────────────────────────────────────────────────────
Same separation of concerns as engine.py (the Clarity Report):

  pandas   ─ ALL math: KPIs (revenue, net income, margin), category rollups,
             uncategorized count, duplicate / double-swipe detection.
  Claude   ─ ONLY prose + labels via tool_use (returns JSON): the per-line
             "What it was / Why this category" notes, the assigned category,
             "What changed", "Miscategorizations we caught", "The One Thing".
  Jinja2   ─ ALL document structure (templates/auto_ledger.html.j2).
  Resend   ─ email delivery with the HTML report.

Three product tiers drive which sections render:
  starter ─ Glance + Transactions + What Changed/Caught + One Thing
  growth  ─ + Quarterly Tax Estimate
  pro     ─ + Connected Accounts + Custom Rules Applied

CSV format  (uploads/<safe_email>.csv)
─────────────────────────────────────────────────────────────────────────────
Rows whose first cell starts with `_` are metadata. A row equal to the literal
header `Date,Description,Amount[,Account]` (case-insensitive) marks the start of
the transaction ledger; every row after it is one transaction.

Example:
  _Business Name,Blue Ridge Comfort Systems LLC
  _Owner Name,Dale
  _Industry,HVAC
  _Location,Columbus GA
  _Month,May 2026
  _Tier,growth
  _Prior Revenue,52490
  _Prior Margin,17.4
  _Uncategorized,47
  Date,Description,Amount,Account
  2026-05-03,ACH deposit · ServiceTitan payout ••••8841,14260,Operating ••••4021
  2026-05-07,Carrier Enterprise · invoice #CE-20418,-3940,Operating ••••4021
  ...

Amounts are signed: positive = money in, negative = money out.
"""

import os
import re
import json
import base64
from pathlib import Path
from datetime import datetime, date, timedelta

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR      = Path(__file__).resolve().parent
UPLOADS_DIR   = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads")
REPORTS_DIR   = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports")
TEMPLATES_DIR = BASE_DIR

PRODUCT_NAME    = "Auto Ledger"
PRODUCT_TAGLINE = "Bookkeeping that explains itself"

TIER_LABELS = {"starter": "Starter", "growth": "Growth", "pro": "Pro"}

# Rough blended set-aside rate for the quarterly estimate (Growth+).
# Deliberately conservative; the report frames it as "set aside", not "owed".
_FED_RATE = 0.15
_STATE_RATE = 0.05
_SE_RATE = 0.092  # ~ employer-half of SE tax on net, simplified

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_PROMPT_DELIMITER_RE = re.compile(r'<<<[A-Z_]*>>>')


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _safe_email(email: str) -> str:
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', local)}_at_{_SAFE_CHAR_RE.sub('_', domain)}"


def _sanitize(value: str, max_len: int = 300) -> str:
    value = _CTRL_CHARS_RE.sub('', str(value))
    value = _PROMPT_DELIMITER_RE.sub('', value)
    return value[:max_len].strip()


def _report_slug(business_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (business_name or "").lower()).strip("_")
    return slug or "report"


def _money(n: float) -> str:
    """$58,420 with no cents; negatives as −$3,940 (figure-dash)."""
    sign = "−" if n < 0 else ""
    return f"{sign}${abs(n):,.0f}"


def _signed_amount(n: float) -> str:
    return (f"+${n:,.0f}" if n > 0 else f"−${abs(n):,.0f}")


# ── Step 1: CSV ingestion ───────────────────────────────────────────────────────

_HEADER_TOKENS = {"date", "description", "amount"}


def _load_ledger(customer_email: str):
    path = UPLOADS_DIR / f"{_safe_email(customer_email)}.csv"
    return load_ledger_path(path)


def load_ledger_path(path: Path):
    """Parse a ledger CSV into (transactions_df, meta_dict). Public for demo use.

    Rows are ragged (metadata rows have 2 cells, transaction rows have 3-4), so
    we parse with the csv module rather than pandas' fixed-width reader.
    """
    import csv
    path = Path(path)
    if not path.exists():
        print(f"[AutoLedger] ERROR - no CSV found at: {path}")
        return None, {}

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))

    meta = {}
    txn_rows = []
    in_ledger = False
    for row in rows:
        if not row:
            continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            key = first.lstrip("_").strip()
            val = str(row[1]).strip() if len(row) > 1 else ""
            meta[key] = val
            continue
        cells = [str(c).strip() for c in row]
        # Detect the ledger header row.
        if not in_ledger:
            lowered = {c.lower() for c in cells[:3]}
            if _HEADER_TOKENS.issubset(lowered):
                in_ledger = True
            continue
        if not first:  # skip blank rows
            continue
        txn_rows.append(cells)

    if not txn_rows:
        print("[AutoLedger] ERROR - no transaction rows found after header.")
        return None, meta

    cols = ["Date", "Description", "Amount", "Account"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in txn_rows]
    df = pd.DataFrame(norm, columns=cols)
    df["Amount"] = pd.to_numeric(
        df["Amount"].astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"
    ).fillna(0.0)
    df = df.reset_index(drop=True)
    print(f"[AutoLedger] Loaded {len(df)} transactions from {path.name}")
    return df, meta


# ── Step 2: all math in pandas ──────────────────────────────────────────────────

def _fmt_date(s: str) -> str:
    """Render '2026-05-03' as 'May 03'. Pass through if unparseable."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s.strip(), fmt).strftime("%b %d")
        except ValueError:
            continue
    return s.strip()


def _detect_duplicates(df: pd.DataFrame) -> list:
    """Same absolute amount + overlapping merchant token within 5 days = likely double-swipe."""
    dups = []
    parsed = []
    for i, r in df.iterrows():
        d = None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
            try:
                d = datetime.strptime(str(r["Date"]).strip(), fmt).date()
                break
            except ValueError:
                continue
        parsed.append((i, d, float(r["Amount"]), str(r["Description"])))
    for a in range(len(parsed)):
        for b in range(a + 1, len(parsed)):
            ia, da, aa, na = parsed[a]
            ib, db, ab, nb = parsed[b]
            if aa == 0 or abs(aa) != abs(ab):
                continue
            tok_a = set(re.findall(r"[A-Za-z]{4,}", na.lower()))
            tok_b = set(re.findall(r"[A-Za-z]{4,}", nb.lower()))
            if not (tok_a & tok_b):
                continue
            if da and db and abs((da - db).days) <= 5:
                dups.append({"amount": abs(aa), "desc": na, "merchant": " ".join(sorted(tok_a & tok_b))})
    return dups


def _calculate_metrics(df: pd.DataFrame, meta: dict) -> dict:
    # Computed from the ledger by default. The transaction table the customer
    # sees may be a curated highlight, so full-month totals can be supplied via
    # `_Revenue` / `_Net Income` metadata (e.g. straight from their books).
    inflow  = float(df.loc[df["Amount"] > 0, "Amount"].sum())
    outflow = float(df.loc[df["Amount"] < 0, "Amount"].sum())  # negative
    net     = inflow + outflow

    rev_override = _to_float(meta.get("Revenue", ""))
    net_override = meta.get("Net Income", "")
    if rev_override:
        inflow = rev_override
    if str(net_override).strip():
        net = _to_float(net_override)
        outflow = net - inflow
    margin  = (net / inflow * 100) if inflow > 0 else 0.0

    prior_rev    = _to_float(meta.get("Prior Revenue", ""))
    prior_margin = _to_float(meta.get("Prior Margin", ""))
    rev_change     = inflow - prior_rev if prior_rev else 0.0
    rev_change_pct = (rev_change / prior_rev * 100) if prior_rev else 0.0

    uncat = _to_float(meta.get("Uncategorized", "")) or 0.0

    print(f"[AutoLedger] Revenue ${inflow:,.0f} | Net ${net:,.0f} ({margin:.1f}% margin) | "
          f"{len(df)} txns | {int(uncat)} uncategorized cleared")

    return {
        "inflow": inflow, "outflow": outflow, "net": net, "margin": margin,
        "prior_rev": prior_rev, "prior_margin": prior_margin,
        "rev_change": rev_change, "rev_change_pct": rev_change_pct,
        "uncategorized": int(uncat),
        "duplicates": _detect_duplicates(df),
        "txn_count": len(df),
    }


def _to_float(s) -> float:
    try:
        return float(str(s).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _quarterly_tax(metrics: dict, meta: dict) -> dict:
    """Growth+ : set-aside estimate from net income run-rate (3 months)."""
    monthly_net = max(metrics["net"], 0.0)
    quarter_net = monthly_net * 3
    federal = quarter_net * _FED_RATE
    state   = quarter_net * _STATE_RATE
    se      = quarter_net * _SE_RATE
    total   = federal + state + se
    period  = _next_quarter_label(meta.get("Month", ""))
    return {
        "period": period,
        "federal": _money(federal), "state": _money(state),
        "se": _money(se), "total": _money(total),
        "_total_num": total, "_quarter_net": quarter_net,
    }


def _next_quarter_label(month_str: str) -> str:
    try:
        dt = datetime.strptime(month_str.strip(), "%B %Y")
    except ValueError:
        return "next quarter"
    q = (dt.month - 1) // 3 + 1
    return f"Q{q} {dt.year} · due {_quarter_due(q, dt.year)}"


def _quarter_due(q: int, year: int) -> str:
    due = {1: f"Apr 15, {year}", 2: f"Jun 15, {year}",
           3: f"Sep 15, {year}", 4: f"Jan 15, {year + 1}"}
    return due.get(q, "")


# ── Step 3: Claude via tool_use — categories + prose only ───────────────────────

AUTO_LEDGER_TOOL = {
    "name": "write_auto_ledger_report",
    "description": (
        "Categorize each bank transaction and write its plain-English explanation, "
        "then write the report narrative. All dollar figures are pre-calculated and "
        "supplied to you — never invent or alter a number. Return prose only: no "
        "markdown, no tables, no bullet characters."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "transactions": {
                "type": "array",
                "description": "One entry per supplied transaction, in the SAME ORDER and SAME COUNT.",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "0-based index of the transaction as supplied."},
                        "category": {"type": "string", "description": "Short ledger category, e.g. 'Service Revenue', 'COGS — Equipment', 'Payroll', 'Vehicle & Fuel', 'Supplies', 'Advertising', 'Bank Charges', 'Owner's Draw'."},
                        "what_it_was": {"type": "string", "description": "1 sentence: what this transaction actually was, in plain English. No leading label."},
                        "why_category": {"type": "string", "description": "1 sentence: why it lands in that category and what it means for the books. No leading label."},
                    },
                    "required": ["index", "category", "what_it_was", "why_category"],
                },
            },
            "what_changed": {
                "type": "array", "items": {"type": "string"},
                "description": "2-3 short paragraphs on what changed this month. Each may start with a bolded lead phrase wrapped in <b>...</b>. Reference the supplied revenue/margin numbers verbatim.",
            },
            "miscatches": {
                "type": "array", "items": {"type": "string"},
                "description": "1-3 miscategorizations caught. Each is one sentence describing the catch and the fix. Wrap the corrected category in <span class=\"fix\">...</span> and any prior wrong category in <span class=\"from\">...</span>. Use the supplied duplicate hints where relevant.",
            },
            "one_thing_title": {"type": "string", "description": "Short imperative headline for the single highest-value cleanup, e.g. 'Move your van loan payment off the credit card.'"},
            "one_thing_body": {"type": "string", "description": "2-3 sentences. The one cleanup with real dollars attached this month. Wrap any dollar figure in <span class=\"dollar\">...</span>. Use only supplied numbers; you may state a plausible interest/APR figure only if framed as an estimate."},
        },
        "required": ["transactions", "what_changed", "miscatches", "one_thing_title", "one_thing_body"],
    },
}


def _build_prompt(df, meta, metrics):
    biz      = _sanitize(meta.get("Business Name", "the business"), 200)
    industry = _sanitize(meta.get("Industry", "small business"), 100)
    location = _sanitize(meta.get("Location", ""), 150)
    month    = _sanitize(meta.get("Month", ""), 30)

    lines = []
    for i, r in df.iterrows():
        lines.append(f"  [{i}] {r['Date']} | {r['Description']} | {_signed_amount(r['Amount'])}"
                     + (f" | acct {r['Account']}" if str(r['Account']).strip() else ""))
    dup_lines = [f"  - ${d['amount']:,.0f} possible double-swipe involving '{d['merchant']}': {d['desc']}"
                 for d in metrics["duplicates"]] or ["  (none detected by the engine)"]

    return (
        f"Business: {biz} ({industry}{', ' + location if location else ''}). Month: {month}.\n\n"
        f"Pre-calculated figures (use verbatim, never recompute):\n"
        f"  Revenue (money in): {_money(metrics['inflow'])}\n"
        f"  Net income: {_money(metrics['net'])} ({metrics['margin']:.1f}% margin)\n"
        f"  Prior revenue: {_money(metrics['prior_rev'])} | prior margin: {metrics['prior_margin']:.1f}%\n"
        f"  Revenue change: {_money(metrics['rev_change'])} ({metrics['rev_change_pct']:+.1f}%)\n"
        f"  Uncategorized cleared this month: {metrics['uncategorized']} → 0\n\n"
        f"Transactions to categorize and explain (keep order and count exactly):\n"
        + "\n".join(lines)
        + "\n\nEngine-detected duplicate/double-swipe hints:\n"
        + "\n".join(dup_lines)
        + "\n\nWrite for the owner of the business directly. Plain English, no jargon, "
        "no accounting lectures. Every transaction explanation must be specific to that line."
    )


_SYSTEM_PROMPT = (
    "You are Auto Ledger, EchoFrame's bookkeeping engine. You categorize each "
    "transaction and explain it to a small-business owner in plain English — what it "
    "was and why it lands where it does. You are precise and never condescending.\n\n"
    "RULES:\n"
    "  • All dollar figures are supplied by a verified engine. Copy them exactly; never "
    "invent, re-round, or sum numbers yourself.\n"
    "  • Return exactly one entry per supplied transaction, in the same order, with the "
    "matching index.\n"
    "  • 'what_it_was' and 'why_category' are each ONE sentence with no leading label "
    "(the template adds 'What it was:' / 'Why this category:').\n"
    "  • Categories are the owner's books, not tax codes. Money in from the core service "
    "is 'Service Revenue', not 'Other Income'. Resold equipment is 'COGS — Equipment'. "
    "Owner transfers to personal accounts are 'Owner's Draw', never an expense.\n"
    "  • Be concrete and useful. No filler, no hedging, no markdown."
)


def _generate_narrative(df, meta, metrics):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=_SYSTEM_PROMPT,
        tools=[AUTO_LEDGER_TOOL],
        tool_choice={"type": "tool", "name": "write_auto_ledger_report"},
        messages=[{"role": "user", "content": _build_prompt(df, meta, metrics)}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "write_auto_ledger_report":
            return block.input
    raise RuntimeError("[AutoLedger] Claude returned no tool_use block.")


# ── Step 4: assemble the Jinja2 context ─────────────────────────────────────────

def _build_context(df, meta, metrics, prose, tier: str, is_sample: bool) -> dict:
    tier = (tier or "starter").lower()
    tier = tier if tier in TIER_LABELS else "starter"

    # Index prose by transaction index for safe alignment.
    by_index = {int(t.get("index", n)): t for n, t in enumerate(prose["transactions"])}

    transactions = []
    for i, r in df.iterrows():
        t = by_index.get(i, {})
        amt = float(r["Amount"])
        transactions.append({
            "date": _fmt_date(str(r["Date"])),
            "title": str(r["Description"]),
            "what_was": t.get("what_it_was", ""),
            "why_category": t.get("why_category", ""),
            "category": t.get("category", "Uncategorized"),
            "amount_str": _signed_amount(amt),
            "amt_class": "amt-in" if amt > 0 else "amt-out",
        })

    rev_delta_cls = "up" if metrics["rev_change"] >= 0 else "down"
    arrow = "▲" if metrics["rev_change"] >= 0 else "▼"
    if metrics["prior_rev"]:
        rev_delta = (f"{arrow} {abs(metrics['rev_change_pct']):.1f}% &nbsp;·&nbsp; "
                     f"{_signed_amount(metrics['rev_change'])} vs prior")
    else:
        rev_delta = "this month"

    margin_delta_cls = "up" if metrics["margin"] >= metrics["prior_margin"] else "down"
    if metrics["prior_margin"]:
        margin_arrow = "▲" if metrics["margin"] >= metrics["prior_margin"] else "▼"
        margin_delta = (f"{margin_arrow} {metrics['margin']:.1f}% margin &nbsp;·&nbsp; "
                        f"{'up' if metrics['margin'] >= metrics['prior_margin'] else 'down'} "
                        f"from {metrics['prior_margin']:.1f}%")
    else:
        margin_delta = f"{metrics['margin']:.1f}% margin"

    kpis = [
        {"label": "Revenue", "value": _money(metrics["inflow"]),
         "delta_class": rev_delta_cls, "delta_text": rev_delta},
        {"label": "Net Income", "value": _money(metrics["net"]),
         "delta_class": margin_delta_cls, "delta_text": margin_delta},
        {"label": "Uncategorized Cleared", "value": f"{metrics['uncategorized']} → 0",
         "delta_class": "flat", "delta_text": f"All {metrics['uncategorized']} sorted &amp; explained this month"},
    ]

    ctx = {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME,
        "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""),
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "is_sample": is_sample,
        "vs_label": (f"vs. prior month" if metrics["prior_rev"] else ""),
        "kpis": kpis,
        "transactions": transactions,
        "what_changed": prose["what_changed"],
        "miscatches": prose["miscatches"],
        "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]},
        "tax_estimate": None,
        "accounts": None,
        "custom_rules": None,
    }

    # ── Tier add-ons ──
    if tier in ("growth", "pro"):
        tax = _quarterly_tax(metrics, meta)
        tax["note"] = (
            f"Set aside <b>{tax['total']}</b> for {tax['period'].split(' · ')[0]} based on this "
            f"month's net income at run-rate. This is a planning estimate, not a filing — your "
            f"CPA-ready export ships with the figures behind it."
        )
        ctx["tax_estimate"] = tax

    if tier == "pro":
        ctx["accounts"] = _accounts_summary(df, meta)
        ctx["custom_rules"] = _custom_rules(meta)

    return ctx


def _accounts_summary(df, meta) -> list:
    """Pro: roll up transaction counts per connected account."""
    accounts = []
    if "Account" in df.columns and df["Account"].astype(str).str.strip().any():
        counts = df[df["Account"].astype(str).str.strip() != ""].groupby("Account").size()
        for name, n in counts.items():
            atype = "Credit Card" if re.search(r"card|visa|amex|mastercard", name, re.I) else "Bank"
            accounts.append({"name": name, "type": atype, "txn_count": int(n), "status": "Reconciled"})
    if not accounts:  # fallback single account
        accounts = [{"name": "Primary Operating Account", "type": "Bank",
                     "txn_count": len(df), "status": "Reconciled"}]
    return accounts


def _custom_rules(meta) -> list:
    """Pro: pull custom rules from metadata (_Rule lines), else show sensible defaults."""
    rules = []
    for k, v in meta.items():
        if k.lower().startswith("rule") and v.strip():
            rules.append(v.strip())
    if not rules:
        rules = [
            "<b>Fuel & fleet cards</b> auto-post to Vehicle &amp; Fuel — no receipt chasing.",
            "<b>Equipment over $500</b> is capitalized, not expensed to Supplies.",
            "<b>Owner transfers</b> to personal accounts always route to Owner's Draw.",
        ]
    return rules


# ── Step 5: render, persist, deliver ────────────────────────────────────────────

def _render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    return env.get_template("auto_ledger.html.j2").render(**ctx)


def _save_report(meta: dict, tier: str, html: str) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    slug = _report_slug(meta.get("Business Name", ""))
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"EchoFrame_AutoLedger_{tier}_{slug}_{ts}.html"
    path.write_text(html, encoding="utf-8")
    print(f"[AutoLedger] Report saved -> {path.name}")
    return str(path)


def _send_report_email(customer_email, owner_name, html_bytes, meta, tier):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", datetime.now().strftime("%B %Y")).strip()
    biz   = meta.get("Business Name", "your business").strip() or "your business"
    greet = (owner_name or "").strip() or "there"
    fname = f"EchoFrame_AutoLedger_{month.replace(' ', '_')}.html"
    email_from = os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>")
    body = (
        f"<p>Hi {greet},</p>"
        f"<p>Your {month} Auto Ledger report for {biz} is attached and shown below — every "
        f"transaction categorized and explained in plain English, with the one cleanup worth "
        f"your attention this month.</p>"
        f"<p>Reply with any questions.</p>"
        f"<p>— EchoFrame<br><span style=\"color:#6B7280;font-size:12px;\">Business intelligence, "
        f"not accounting software. Informational only; not accounting, tax, legal, or investment advice.</span></p>"
    )
    resend.Emails.send({
        "from": email_from,
        "to": [customer_email],
        "subject": f"Your {month} Auto Ledger — {biz}".strip(),
        "html": body,
        "attachments": [{
            "filename": fname,
            "content": base64.b64encode(html_bytes).decode("ascii"),
            "content_type": "text/html",
        }],
    })
    print("[AutoLedger] Report email dispatched.")  # no PII in logs


# ── Public entry point ──────────────────────────────────────────────────────────

def generate_auto_ledger_report(
    customer_email: str,
    customer_name: str = "Client",
    tier: str = "",
    send_email: bool = True,
) -> str:
    df, meta = _load_ledger(customer_email)
    if df is None:
        return ""
    if not meta.get("Owner Name", "").strip():
        meta["Owner Name"] = customer_name.strip() or "Client"
    tier = (tier or meta.get("Tier", "starter")).lower()

    metrics = _calculate_metrics(df, meta)
    prose   = _generate_narrative(df, meta, metrics)
    ctx     = _build_context(df, meta, metrics, prose, tier, is_sample=False)
    html    = _render_html(ctx)
    path    = _save_report(meta, ctx["tier"], html)

    if send_email:
        _send_report_email(customer_email, meta["Owner Name"],
                           Path(path).read_bytes(), meta, ctx["tier"])
    print(f"[AutoLedger] Pipeline complete -> {customer_email} ({ctx['tier']})")
    return path


def render_from_csv(csv_path, tier: str, prose: dict, is_sample: bool = True) -> str:
    """Offline render path (no API call): caller supplies the prose dict.
    Used by the demo to preview the template for each tier instantly."""
    df, meta = load_ledger_path(csv_path)
    if df is None:
        return ""
    metrics = _calculate_metrics(df, meta)
    ctx = _build_context(df, meta, metrics, prose, tier, is_sample=is_sample)
    html = _render_html(ctx)
    return _save_report(meta, ctx["tier"], html)
