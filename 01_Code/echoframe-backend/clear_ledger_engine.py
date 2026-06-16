"""
EchoFrame — Clear Ledger report engine
─────────────────────────────────────────────────────────────────────────────
pandas  ─ total overdue (sum), aging pills, oldest-balance ranking.
Claude  ─ the 3 nudge-stage example messages, the method note, and The One Thing.
Jinja2  ─ templates/clear_ledger.html.j2
Resend  ─ delivery.

Tiers: starter ($49, ≤25 invoices) / growth ($99, unlimited + human handoff).

CSV: `_` meta rows + header containing `Customer`, `Invoice`, `Amount`, then rows:
  Customer, Detail, Invoice, Amount, Days Overdue, Next Action, When
Meta: _Collected, _Cleared Count, _Avg Days, _Prior Days.
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR      = Path(__file__).resolve().parent
UPLOADS_DIR   = BASE_DIR / "uploads"
REPORTS_DIR   = BASE_DIR / "reports"
TEMPLATES_DIR = BASE_DIR / "templates"

PRODUCT_NAME    = "Clear Ledger"
PRODUCT_TAGLINE = "Invoice follow-up & accounts-receivable recovery"
TIER_LABELS = {"starter": "Starter", "growth": "Growth"}

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_PROMPT_DELIMITER_RE = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"customer", "invoice", "amount"}


def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL_CHARS_RE.sub('', str(v)); v = _PROMPT_DELIMITER_RE.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _to_float(s):
    try: return float(str(s).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError): return 0.0
def _money(n): return f"{'−' if n < 0 else ''}${abs(n):,.0f}"
def _int(s): return int(_to_float(s))


# ── ingestion ──
def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")

def load_path(path):
    path = Path(path)
    if not path.exists():
        print(f"[ClearLedger] ERROR - no CSV at {path}"); return None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    meta, rrows, inlist = {}, [], False
    for row in rows:
        if not row: continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""; continue
        cells = [str(c).strip() for c in row]
        if not inlist:
            if _HEADER_TOKENS.issubset({c.lower() for c in cells}): inlist = True
            continue
        if not first: continue
        rrows.append(cells)
    if not rrows:
        print("[ClearLedger] ERROR - no invoice rows"); return None, meta
    cols = ["Customer", "Detail", "Invoice", "Amount", "Days Overdue", "Next Action", "When"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in rrows]
    df = pd.DataFrame(norm, columns=cols)
    df["AmountNum"] = df["Amount"].map(_to_float)
    df["DaysNum"]   = df["Days Overdue"].map(_int)
    df = df.reset_index(drop=True)
    print(f"[ClearLedger] Loaded {len(df)} invoices from {path.name}")
    return df, meta


# ── math ──
def _pill(days):
    if days >= 30: return "late"
    if days < 10:  return "fresh"
    return "warn"

def _metrics(df, meta):
    total_overdue = float(df["AmountNum"].sum())
    top_i = int(df["DaysNum"].idxmax())
    collected = _to_float(meta.get("Collected", ""))
    cleared   = _int(meta.get("Cleared Count", "")) if meta.get("Cleared Count", "").strip() else None
    avg_days  = _int(meta.get("Avg Days", "")) if meta.get("Avg Days", "").strip() else None
    prior_days = _int(meta.get("Prior Days", "")) if meta.get("Prior Days", "").strip() else None
    print(f"[ClearLedger] overdue ${total_overdue:,.0f} across {len(df)} | collected ${collected:,.0f}")
    return {"total_overdue": total_overdue, "open_count": len(df), "top_i": top_i,
            "collected": collected, "cleared": cleared, "avg_days": avg_days,
            "prior_days": prior_days}


# ── Claude ──
CLEAR_LEDGER_TOOL = {
    "name": "write_clear_ledger_report",
    "description": "Write the nudge-stage example messages, method note, and One Thing for an "
                   "invoice-collections report. All dollar figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "stage_quotes": {"type": "array", "items": {"type": "string"},
            "description": "Exactly 3 short example messages in quotes: (1) friendly day-3 reminder, "
                           "(2) firm day-14 follow-up, (3) final day-30 notice. Each references a real "
                           "invoice number and amount from the data. Professional, relationship-preserving."},
        "method_note": {"type": "string", "description": "One paragraph on how the sequence works "
                        "(friendly day 3, firm day 14, final day 30; auto-resolve; human handoff at "
                        "escalation) and the cycle result (amount collected, days-to-pay improvement). "
                        "Use supplied numbers. May use <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Imperative headline for the single overdue invoice to act on now."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences: the oldest/largest balance, its age, why it crossed into human handoff, the action, and the % of total overdue it represents. Wrap dollar/percent figures in <span class=\"dollar\">...</span>."},
    }, "required": ["stage_quotes", "method_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Clear Ledger, EchoFrame's receivables engine. You recover overdue invoices while "
           "protecting the customer relationship. All dollar figures are supplied by a verified engine — "
           "copy them exactly, never invent. Professional, firm, never threatening. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    lines = [f"  {r['Customer']} | {r['Invoice']} | {_money(r['AmountNum'])} | {r['DaysNum']} days overdue"
             for _, r in df.iterrows()]
    top = df.loc[m["top_i"]]
    return (f"Business: {biz}. Month: {_sanitize(meta.get('Month',''),30)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Total overdue: {_money(m['total_overdue'])} across {m['open_count']} invoices\n"
            f"  Collected this cycle: {_money(m['collected'])}\n"
            f"  Avg days to pay: {m['avg_days']} (was {m['prior_days']})\n"
            f"  Oldest/largest: {top['Customer']} {top['Invoice']} {_money(top['AmountNum'])} at {top['DaysNum']} days\n\n"
            f"Open invoices:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. The One Thing is the oldest+largest balance that has crossed into "
            "human-handoff territory.")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2000, system=_SYSTEM,
        tools=[CLEAR_LEDGER_TOOL], tool_choice={"type": "tool", "name": "write_clear_ledger_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[ClearLedger] no tool_use")


# ── context ──
def _source_line(meta):
    return (f"Based on {_sanitize(meta.get('Business Name','the client'),120)}'s connected invoicing data · "
            f"{_sanitize(meta.get('Month',''),30)} billing cycle · EchoFrame Clear Ledger.")

def _context(df, meta, m, prose, tier, is_sample):
    tier = (tier or "starter").lower(); tier = tier if tier in TIER_LABELS else "starter"
    top_i = m["top_i"]
    rows = []
    for i in df["DaysNum"].sort_values(ascending=False, kind="stable").index:
        r = df.loc[i]
        rows.append({"customer": str(r["Customer"]), "detail": str(r["Detail"]).strip(),
                     "invoice": str(r["Invoice"]), "amount": _money(r["AmountNum"]),
                     "days": r["DaysNum"], "pill_class": _pill(r["DaysNum"]),
                     "action": str(r["Next Action"]).strip(), "when": str(r["When"]).strip(),
                     "go": (i == top_i), "top": (i == top_i)})
    kpis = [
        {"label": "Total Overdue", "value": _money(m["total_overdue"]), "unit": "",
         "delta_class": "down", "delta_text": f"▲ across {m['open_count']} past-due invoices"},
        {"label": "Collected This Month", "value": _money(m["collected"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {m['cleared'] or 0} invoices cleared by the sequence"},
        {"label": "Avg Days to Pay", "value": str(m["avg_days"] or "—"), "unit": "days",
         "delta_class": "up",
         "delta_text": (f"▼ down from {m['prior_days']} before Clear Ledger" if m["prior_days"] else "since Clear Ledger")},
    ]
    q = prose["stage_quotes"] + ["", "", ""]
    stages = [
        {"name": "Friendly", "day": "Day 3 past due",  "tone": "Warm reminder",   "quote": q[0]},
        {"name": "Firm",     "day": "Day 14 past due", "tone": "Direct follow-up", "quote": q[1]},
        {"name": "Final",    "day": "Day 30 past due", "tone": "Final notice",     "quote": q[2]},
    ]
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "tier": tier, "tier_label": TIER_LABELS[tier],
            "is_sample": is_sample, "open_count": m["open_count"], "kpis": kpis, "rows": rows,
            "total_overdue": _money(m["total_overdue"]), "stages": stages,
            "method_note": prose["method_note"], "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


# ── render / persist / deliver ──
def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("clear_ledger.html.j2").render(**ctx)

def _save(meta, tier, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_ClearLedger_{tier}_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[ClearLedger] Report saved -> {p.name}"); return str(p)

def _email(email, owner, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>"),
        "to": [email], "subject": f"Your {month} Clear Ledger — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Clear Ledger report for {biz} is "
                f"attached — every overdue invoice, where it sits in the follow-up sequence, and the one to act on.</p>"
                f"<p>— EchoFrame</p>",
        "attachments": [{"filename": f"EchoFrame_ClearLedger_{month.replace(' ','_')}.html",
                         "content": base64.b64encode(html_bytes).decode("ascii"), "content_type": "text/html"}]})
    print("[ClearLedger] Report email dispatched.")


def generate_clear_ledger_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    tier = (tier or meta.get("Tier", "starter")).lower()
    m = _metrics(df, meta); prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, tier, is_sample=False)
    html = _render(ctx); path = _save(meta, ctx["tier"], html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[ClearLedger] Pipeline complete -> {customer_email} ({ctx['tier']})")
    return path

def render_from_csv(csv_path, tier, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, (tier or "starter").lower(), _render(_context(df, meta, m, prose, tier, is_sample)))
