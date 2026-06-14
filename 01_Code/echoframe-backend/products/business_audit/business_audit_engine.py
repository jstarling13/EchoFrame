"""
EchoFrame - Business Audit Report engine
-----------------------------------------------------------------------------
Premium ($499-799) front-door consulting deliverable: a full business audit in
Clarity's style but far deeper (target 5,000-7,000 words). Built from the
marketing system-prompt spec in 02_Marketing/revenue_engine_v4.html.

pandas/py - deterministic financial metrics from the 3-month financials table
            (avg revenue, avg profit, margin, revenue trend).
Claude    - the full long-form audit (Sonnet 4.6, large tool schema): health
            score + subscores, financial/market/operational analysis, ranked
            recommendations, quick wins. Figures supplied; prose generated.
Jinja2    - templates/business_audit.html.j2 ; Resend - delivery.

INPUT CSV (questionnaire + financials table):
  Leading `_`-prefixed meta rows:
    _Business Name, _Industry, _Location, _Years, _Employees, _Competitors,
    _Challenge, _Owner Name, _Month
  Then a header row containing: Month, Revenue, Expenses
  Then one row per month:  Month, Revenue, Expenses
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads")
REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports")
TEMPLATES_DIR = BASE_DIR

PRODUCT_NAME = "Business Audit Report"
PRODUCT_TAGLINE = "A consulting-grade audit of your whole business"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"revenue", "expenses"}


def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"

def _sanitize(v, n=600):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()

def _slug(b):
    s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"

def _to_float(s):
    try:
        return float(str(s).replace("$", "").replace(",", "").replace("k", "000").strip())
    except (ValueError, AttributeError):
        return 0.0

def _money(n): return f"${n:,.0f}"


def _load(email):
    return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")

def load_path(path):
    path = Path(path)
    if not path.exists():
        print(f"[BusinessAudit] ERROR - no CSV at {path}"); return None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    meta, lrows, inlist = {}, [], False
    for row in rows:
        if not row:
            continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""
            continue
        cells = [str(c).strip() for c in row]
        if not inlist:
            if _HEADER_TOKENS.issubset({c.lower() for c in cells}):
                inlist = True
            continue
        if not first:
            continue
        lrows.append(cells)
    cols = ["Month", "Revenue", "Expenses"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in lrows]
    df = pd.DataFrame(norm, columns=cols).reset_index(drop=True)
    if not df.empty:
        df["Rev"] = df["Revenue"].map(_to_float)
        df["Exp"] = df["Expenses"].map(_to_float)
        df["Profit"] = df["Rev"] - df["Exp"]
    print(f"[BusinessAudit] Loaded {len(df)} financial periods from {path.name}")
    return df, meta


def _metrics(df, meta):
    if df is None or df.empty:
        # Fall back to the single monthly-revenue figure from the questionnaire.
        rev = _to_float(meta.get("Revenue", "0"))
        return {"avg_revenue": rev, "avg_profit": 0.0, "margin": 0.0,
                "trend_pct": 0.0, "periods": 0}
    avg_rev = float(df["Rev"].mean())
    avg_profit = float(df["Profit"].mean())
    margin = round(avg_profit / avg_rev * 100, 1) if avg_rev else 0.0
    first, last = float(df["Rev"].iloc[0]), float(df["Rev"].iloc[-1])
    trend = round((last - first) / first * 100, 1) if first else 0.0
    print(f"[BusinessAudit] avg rev {_money(avg_rev)} | avg profit {_money(avg_profit)} "
          f"| margin {margin}% | trend {trend}%")
    return {"avg_revenue": avg_rev, "avg_profit": avg_profit, "margin": margin,
            "trend_pct": trend, "periods": len(df)}


AUDIT_TOOL = {
    "name": "write_business_audit_report",
    "description": (
        "Write a complete, premium Business Audit report for a small business. This is a paid "
        "($499+) consulting-grade deliverable - write with authority, specificity, and directness, "
        "and use numbers throughout. Dollar figures for revenue, profit, and margin are supplied by "
        "a verified engine - use them exactly and build your dollar estimates around them. Total "
        "prose across all fields should be roughly 5,000-7,000 words: full paragraphs, never "
        "one-liners. Name specific problems and specific fixes."
    ),
    "input_schema": {"type": "object", "properties": {
        "health_score": {"type": "object", "properties": {
            "overall": {"type": "integer", "description": "Overall business health score out of 100."},
            "grade": {"type": "string", "description": "Letter grade, e.g. B+, C, A-."},
            "financial": {"type": "integer", "description": "Financial Health subscore 0-25."},
            "financial_note": {"type": "string", "description": "One sentence defending the financial subscore."},
            "market": {"type": "integer", "description": "Market Position subscore 0-25."},
            "market_note": {"type": "string", "description": "One sentence defending the market subscore."},
            "operational": {"type": "integer", "description": "Operational Efficiency subscore 0-25."},
            "operational_note": {"type": "string", "description": "One sentence defending the operational subscore."},
            "growth": {"type": "integer", "description": "Growth Potential subscore 0-25."},
            "growth_note": {"type": "string", "description": "One sentence defending the growth subscore."}},
            "required": ["overall", "grade", "financial", "financial_note", "market", "market_note",
                          "operational", "operational_note", "growth", "growth_note"]},
        "executive_summary": {"type": "array", "items": {"type": "string"},
            "description": "3-4 substantial paragraphs (4-6 sentences each) framing the overall verdict, the biggest risk, and the biggest opportunity."},
        "financial_health": {"type": "object", "properties": {
            "revenue_trend": {"type": "string", "description": "2-3 sentences on the revenue trend, using the supplied figures."},
            "profit_margin": {"type": "string", "description": "2-3 sentences on average profit and margin, using the supplied figures."},
            "risks": {"type": "array", "items": {"type": "object", "properties": {
                "risk": {"type": "string"},
                "detail": {"type": "string", "description": "2-3 sentences with a specific dollar number."}},
                "required": ["risk", "detail"]},
                "description": "The 3 biggest financial risks, each with specific numbers."}},
            "required": ["revenue_trend", "profit_margin", "risks"]},
        "market_position": {"type": "object", "properties": {
            "standing": {"type": "string", "description": "2-3 sentences on where the business sits vs competitors."},
            "market_share_estimate": {"type": "string", "description": "An estimated local market share with a one-phrase basis."},
            "winning": {"type": "array", "items": {"type": "string"}, "description": "2-3 specific places they are winning."},
            "losing": {"type": "array", "items": {"type": "string"}, "description": "2-3 specific places they are losing."}},
            "required": ["standing", "market_share_estimate", "winning", "losing"]},
        "operational_efficiency": {"type": "object", "properties": {
            "strengths": {"type": "array", "items": {"type": "string"}, "description": "3 operational strengths, each a full sentence."},
            "gaps": {"type": "array", "items": {"type": "object", "properties": {
                "gap": {"type": "string"},
                "cost": {"type": "string", "description": "Estimated dollar cost of this gap."}},
                "required": ["gap", "cost"]},
                "description": "3 operational gaps costing money."},
            "biggest_inefficiency": {"type": "string", "description": "2-3 sentences naming the single biggest inefficiency and its dollar estimate."}},
            "required": ["strengths", "gaps", "biggest_inefficiency"]},
        "recommendations": {"type": "array", "items": {"type": "object", "properties": {
            "action": {"type": "string"},
            "why": {"type": "string", "description": "2-3 sentences with numbers on why it matters."},
            "plan": {"type": "array", "items": {"type": "string"}, "description": "A concrete 3-step plan."},
            "expected_impact": {"type": "string", "description": "Quantified expected impact."},
            "time_to_implement": {"type": "string", "description": "e.g. '2-4 weeks'."}},
            "required": ["action", "why", "plan", "expected_impact", "time_to_implement"]},
            "description": "Exactly the top 3 recommendations, ranked by ROI (highest first)."},
        "quick_wins": {"type": "array", "items": {"type": "string"},
            "description": "Exactly 5 quick wins doable in 30 days at low cost. Each one sentence: action and expected benefit."},
        "the_one_move": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Imperative headline for the single highest-priority move."},
            "body": {"type": "string", "description": "4-6 sentences making the case, tied to numbers."}},
            "required": ["title", "body"]},
    }, "required": ["health_score", "executive_summary", "financial_health", "market_position",
                     "operational_efficiency", "recommendations", "quick_wins", "the_one_move"]},
}

_SYSTEM = (
    "You are EchoFrame's senior business consultant producing a premium Business Audit Report for a "
    "small-business owner. Write with authority, specificity, and directness, like a $3,000 "
    "engagement delivered in 48 hours. Use numbers throughout. Revenue, profit, and margin figures "
    "are supplied by a verified engine - use them exactly. Name specific problems and specific fixes. "
    "Plain, confident English - no jargon, no hedging. Write full paragraphs; this is a long, "
    "thorough document. No markdown - the fields are rendered into a styled report."
)


def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    fin_lines = []
    if df is not None and not df.empty:
        for _, r in df.iterrows():
            fin_lines.append(f"  - {r['Month']}: revenue {_money(r['Rev'])}, expenses {_money(r['Exp'])}, profit {_money(r['Profit'])}")
    fin_block = "\n".join(fin_lines) if fin_lines else "  (no monthly breakdown provided)"
    return (
        f"Business: {biz}\n"
        f"Industry: {_sanitize(meta.get('Industry',''),120)}\n"
        f"Location: {_sanitize(meta.get('Location',''),120)}\n"
        f"Years in business: {_sanitize(meta.get('Years',''),20)}\n"
        f"Employees: {_sanitize(meta.get('Employees',''),20)}\n"
        f"Top local competitors: {_sanitize(meta.get('Competitors',''),400)}\n"
        f"Main challenge the owner faces: {_sanitize(meta.get('Challenge',''),400)}\n\n"
        f"Pre-calculated financials (use verbatim):\n"
        f"  Average monthly revenue: {_money(m['avg_revenue'])}\n"
        f"  Average monthly profit: {_money(m['avg_profit'])}\n"
        f"  Average net margin: {m['margin']}%\n"
        f"  Revenue trend across the period: {m['trend_pct']}%\n\n"
        f"Monthly financials:\n{fin_block}\n\n"
        f"Write the complete audit. Cover every section in depth - this is a paid premium deliverable "
        f"and must read as exhaustive and specific. Aim for 5,000-7,000 words total."
    )


def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(
        model=MODEL, max_tokens=MAX_TOKENS, system=_SYSTEM,
        tools=[AUDIT_TOOL],
        tool_choice={"type": "tool", "name": "write_business_audit_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}],
    )
    for b in r.content:
        if b.type == "tool_use":
            return b.input
    raise RuntimeError("[BusinessAudit] no tool_use")


def _context(df, meta, m, prose, is_sample):
    hs = prose.get("health_score", {})
    subscores = [
        {"label": "Financial Health", "value": hs.get("financial", 0), "note": hs.get("financial_note", "")},
        {"label": "Market Position", "value": hs.get("market", 0), "note": hs.get("market_note", "")},
        {"label": "Operational Efficiency", "value": hs.get("operational", 0), "note": hs.get("operational_note", "")},
        {"label": "Growth Potential", "value": hs.get("growth", 0), "note": hs.get("growth_note", "")},
    ]
    kpis = [
        {"label": "Avg Monthly Revenue", "value": _money(m["avg_revenue"]), "is_text": False,
         "sub_class": "flat", "sub": f"Across {m['periods'] or 1} month(s)"},
        {"label": "Avg Net Margin", "value": f"{m['margin']}%", "is_text": True,
         "sub_class": ("down" if m["margin"] >= 10 else "up"),
         "sub": f"{_money(m['avg_profit'])} avg monthly profit"},
        {"label": "Revenue Trend", "value": (("+" if m["trend_pct"] >= 0 else "") + f"{m['trend_pct']}%"),
         "is_text": True, "sub_class": ("down" if m["trend_pct"] >= 0 else "up"),
         "sub": "Start to end of period"},
    ]
    return {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME, "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""), "is_sample": is_sample,
        "kpis": kpis, "subscores": subscores,
        "overall_score": hs.get("overall", 0), "grade": hs.get("grade", ""),
        **prose,
    }


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)),
                      autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("business_audit.html.j2").render(**ctx)

def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_BusinessAudit_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8")
    print(f"[BusinessAudit] Report saved -> {p.name}"); return str(p)

def _email(email, owner, html_bytes, meta):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({
        "from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email],
        "subject": f"Your Business Audit Report - {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your Business Audit Report for {biz} is "
                f"attached - a full, consulting-grade read on your finances, market position, "
                f"operations, and the highest-ROI moves to make next.</p><p>- EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_BusinessAudit_{_slug(biz)}.html")]})
    print("[BusinessAudit] Report email dispatched.")


def generate_business_audit_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None:
        return ""
    if not meta.get("Owner Name", "").strip():
        meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email:
        _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[BusinessAudit] Pipeline complete -> {customer_email}")
    return path


def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None:
        return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
