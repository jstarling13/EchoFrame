"""
EchoFrame - Competitor & Market Landscape Report engine
-----------------------------------------------------------------------------
Premium ($299) deep-dive competitor intelligence report. Clarity-style HTML,
but far more in depth (target 5,000-7,000 words) so it is clearly worth the
price. Built from the marketing system-prompt spec in
02_Marketing/revenue_engine_v4.html.

pandas/py - light derived metrics (competitor count, intensity band, scorecard
            averages) from the questionnaire CSV.
Claude    - the full long-form narrative (Sonnet 4.6, large tool schema with
            many rich sections) - figures/structure supplied, prose generated.
Jinja2    - templates/competitor_landscape.html.j2 ; Resend - delivery.

INPUT CSV (questionnaire + competitor table):
  Leading `_`-prefixed meta rows:
    _Business Name, _Industry, _Location, _Goal, _Strengths, _Weaknesses,
    _Owner Name, _Month
  Then a header row containing: Competitor, Description
  Then one row per competitor:
    Competitor, Description, Pricing Position, Online Presence
"""

import os, re, csv, base64
import csv_utils
import data_quality
import html_safe
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads")
REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports")
TEMPLATES_DIR = BASE_DIR

PRODUCT_NAME = "Competitor & Market Landscape Report"
PRODUCT_TAGLINE = "What the shop across town is doing, and how to beat it"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"competitor", "description"}


def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"

def _sanitize(v, n=600):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()

def _slug(b):
    s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"


def _load(email):
    return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")

def load_path(path):
    path = Path(path)
    if not path.exists():
        print(f"[CompetitorLandscape] ERROR - no CSV at {path}"); return None, {}
    rows = csv_utils.read_rows(path.read_bytes())
    meta, lrows, inlist = {}, [], False
    header_row = []
    for row in rows:
        if not row:
            continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""
            continue
        cells = [str(c).strip() for c in row]
        if not inlist:
            if csv_utils.header_matches(cells, _HEADER_TOKENS):
                header_row = cells
                inlist = True
            continue
        if not first:
            continue
        if csv_utils.looks_like_totals_row(cells):
            continue
        lrows.append(cells)
    if not lrows:
        print("[CompetitorLandscape] ERROR - no competitor rows"); return None, meta
    cols = ["Competitor", "Description", "Pricing Position", "Online Presence"]
    # Rows with MORE cells than columns are the signature of an unquoted thousands
    # separator: "2,300" splits into "2" + "300" and the trailing cell is dropped.
    # Count them so the data-quality gate can flag a possibly-mangled row.
    idx_map = csv_utils.column_index_map(header_row, cols)
    ncols = len(header_row) or len(cols)
    lrows = [csv_utils.repair_overflow_row(r, ncols) for r in lrows]
    overflow_rows = sum(1 for r in lrows if len(r) > ncols)
    norm = [[csv_utils.cell(r, idx_map[k]) for k in range(len(cols))] for r in lrows]
    df = pd.DataFrame(norm, columns=cols).reset_index(drop=True)
    # Record how many rows the parser SAW so the gate can spot silent drops / mis-splits.
    df.attrs["dq_rows_in"] = len(lrows)
    df.attrs["dq_overflow_rows"] = overflow_rows
    print(f"[CompetitorLandscape] Loaded {len(df)} competitors from {path.name}")
    return df, meta


def _metrics(df, meta):
    n = len(df)
    # Intensity band purely from competitor density (deterministic).
    intensity = "Low" if n <= 2 else ("Medium" if n <= 4 else "High")
    print(f"[CompetitorLandscape] {n} competitors | intensity {intensity}")
    return {"competitor_count": n, "intensity": intensity}


COMPETITOR_TOOL = {
    "name": "write_competitor_landscape_report",
    "description": (
        "Write a complete, premium Competitor & Market Landscape report for a small business. "
        "This is a paid ($299) deliverable - write with the depth and specificity of a real "
        "consulting engagement. Be direct about where the client is losing. Name competitors by "
        "name. Use concrete numbers throughout. Total prose across all fields should be roughly "
        "5,000-7,000 words: write full, multi-sentence paragraphs, never one-liners."
    ),
    "input_schema": {"type": "object", "properties": {
        "executive_summary": {"type": "array", "items": {"type": "string"},
            "description": "3-4 substantial paragraphs (4-6 sentences each) opening the report: the competitive situation, where the client stands, the single biggest threat, and the single biggest opportunity."},
        "landscape_overview": {"type": "object", "properties": {
            "environment": {"type": "string", "description": "2-3 sentences describing the competitive environment for this business type in this location."},
            "intensity": {"type": "string", "description": "One of Low / Medium / High, with a one-sentence justification."},
            "hierarchy_position": {"type": "string", "description": "Where this client sits in the local hierarchy (leader / challenger / niche / laggard) and why."},
            "paragraphs": {"type": "array", "items": {"type": "string"},
                "description": "3-4 detailed paragraphs expanding on market structure, demand trends, and what is changing in this local market."}},
            "required": ["environment", "intensity", "hierarchy_position", "paragraphs"]},
        "competitor_profiles": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"},
            "overview": {"type": "string", "description": "2-3 sentence overview of this competitor."},
            "strengths": {"type": "array", "items": {"type": "string"}, "description": "2-4 specific estimated strengths."},
            "weaknesses": {"type": "array", "items": {"type": "string"}, "description": "2-4 specific estimated weaknesses."},
            "pricing_position": {"type": "string", "description": "Budget / Mid-Market / Premium, with a phrase of context."},
            "online_presence": {"type": "string", "description": "Assessment of their online presence strength."},
            "watch": {"type": "string", "description": "The one thing our client should notice about this competitor."},
            "vulnerability": {"type": "string", "description": "Where this competitor is vulnerable - how our client can exploit it."}},
            "required": ["name", "overview", "strengths", "weaknesses", "pricing_position", "online_presence", "watch", "vulnerability"]},
            "description": "One rich profile per competitor provided (and include the client themselves as the first entry if useful)."},
        "scorecard": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"},
            "is_you": {"type": "boolean"},
            "price": {"type": "integer", "description": "1-5"},
            "location": {"type": "integer", "description": "1-5"},
            "online": {"type": "integer", "description": "1-5"},
            "experience": {"type": "integer", "description": "1-5"},
            "quality": {"type": "integer", "description": "1-5"},
            "specialization": {"type": "integer", "description": "1-5"},
            "momentum": {"type": "integer", "description": "1-5"}},
            "required": ["name", "is_you", "price", "location", "online", "experience", "quality", "specialization", "momentum"]},
            "description": "Score the client AND each competitor 1-5 on each dimension. The client row must have is_you=true."},
        "where_winning": {"type": "array", "items": {"type": "object", "properties": {
            "advantage": {"type": "string"},
            "why_customers_value": {"type": "string", "description": "2-3 sentences."},
            "how_to_amplify": {"type": "string", "description": "2-3 sentences on how to protect and amplify it."}},
            "required": ["advantage", "why_customers_value", "how_to_amplify"]},
            "description": "3-5 advantages where the client is winning."},
        "where_losing": {"type": "array", "items": {"type": "object", "properties": {
            "gap": {"type": "string"},
            "which_competitor": {"type": "string", "description": "Which competitor exploits this gap."},
            "monthly_impact": {"type": "string", "description": "Estimated monthly dollar impact, e.g. '$1,800/mo in lost bookings'."},
            "what_to_do": {"type": "string", "description": "2-3 sentences on the fix."}},
            "required": ["gap", "which_competitor", "monthly_impact", "what_to_do"]},
            "description": "3-5 gaps where the client is losing."},
        "things_to_steal": {"type": "array", "items": {"type": "object", "properties": {
            "competitor": {"type": "string"},
            "what_they_do": {"type": "string"},
            "why_it_works": {"type": "string", "description": "2-3 sentences."},
            "how_to_implement": {"type": "array", "items": {"type": "string"}, "description": "3-6 concrete step-by-step actions."},
            "expected_impact": {"type": "string", "description": "Quantified expected impact."}},
            "required": ["competitor", "what_they_do", "why_it_works", "how_to_implement", "expected_impact"]},
            "description": "Exactly the 3 highest-value tactics to steal from competitors."},
        "ninety_day_plan": {"type": "object", "properties": {
            "month1": {"type": "array", "items": {"type": "string"}, "description": "3 quick moves, each 1-2 sentences."},
            "month2": {"type": "array", "items": {"type": "string"}, "description": "2 positioning plays, each 1-2 sentences."},
            "month3": {"type": "array", "items": {"type": "string"}, "description": "1 long-term differentiator, 2-3 sentences."}},
            "required": ["month1", "month2", "month3"]},
        "the_one_move": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Imperative headline for the single most important move."},
            "body": {"type": "string", "description": "4-6 sentences making the case, tied to numbers."}},
            "required": ["title", "body"]},
    }, "required": ["executive_summary", "landscape_overview", "competitor_profiles", "scorecard",
                     "where_winning", "where_losing", "things_to_steal", "ninety_day_plan", "the_one_move"]},
}

_SYSTEM = (
    "You are EchoFrame's market intelligence analyst producing a premium Competitor & Market "
    "Landscape Report for a small-business owner. Write with the confidence, specificity, and depth "
    "of a $3,000 consulting engagement. Be direct about where the client is losing. Name competitors "
    "by name. Use concrete numbers and dollar estimates throughout. Plain, vivid English - no jargon, "
    "no 'leverage' or 'synergy'. Write full paragraphs; this is a long, thorough document, not a "
    "summary. No markdown in your output - the fields are rendered into a styled report."
)


def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    comp_lines = [
        f"  - {r['Competitor']}: {r['Description']}"
        + (f" | pricing: {r['Pricing Position']}" if r['Pricing Position'] else "")
        + (f" | online: {r['Online Presence']}" if r['Online Presence'] else "")
        for _, r in df.iterrows()
    ]
    return (
        f"Business: {biz}\n"
        f"Industry: {_sanitize(meta.get('Industry',''),120)}\n"
        f"Location: {_sanitize(meta.get('Location',''),120)}\n"
        f"Goal the owner wants to achieve: {_sanitize(meta.get('Goal',''),300)}\n"
        f"What the client does better than anyone: {_sanitize(meta.get('Strengths',''),500)}\n"
        f"Where the client knows they fall short: {_sanitize(meta.get('Weaknesses',''),500)}\n\n"
        f"Pre-calculated (use verbatim): {m['competitor_count']} competitors tracked; "
        f"competitive intensity rated {m['intensity']}.\n\n"
        f"Competitors:\n" + "\n".join(comp_lines)
        + "\n\nWrite the complete report. Cover every section in depth - this is a paid premium "
        "deliverable and must read as exhaustive and specific. Aim for 5,000-7,000 words total."
    )


def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(
        model=MODEL, max_tokens=MAX_TOKENS, system=_SYSTEM,
        tools=[COMPETITOR_TOOL],
        tool_choice={"type": "tool", "name": "write_competitor_landscape_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}],
    )
    for b in r.content:
        if b.type == "tool_use":
            return b.input
    raise RuntimeError("[CompetitorLandscape] no tool_use")


def _context(df, meta, m, prose, is_sample):
    score_keys = ["price", "location", "online", "experience", "quality", "specialization", "momentum"]
    scorecard = []
    for row in prose.get("scorecard", []):
        vals = [int(row.get(k, 0) or 0) for k in score_keys]
        total = sum(vals)
        scorecard.append({
            "name": row.get("name", ""), "is_you": bool(row.get("is_you")),
            "scores": vals, "total": total,
            "avg": round(total / len(score_keys), 1) if score_keys else 0,
        })
    kpis = [
        {"label": "Competitors Tracked", "value": str(m["competitor_count"]), "is_text": False,
         "sub_class": "flat", "sub": "In your local market"},
        {"label": "Competitive Intensity", "value": m["intensity"], "is_text": True,
         "sub_class": ("up" if m["intensity"] == "High" else "flat"),
         "sub": "How hard the field is fighting"},
        {"label": "Tactics To Steal", "value": str(len(prose.get("things_to_steal", []))), "is_text": False,
         "sub_class": "down", "sub": "High-value moves identified"},
    ]
    return {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME, "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""), "is_sample": is_sample,
        "kpis": kpis,
        "score_dims": ["Price", "Location", "Online", "Experience", "Quality", "Special.", "Momentum"],
        "scorecard": scorecard,
        **prose,
    }


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)),
                      autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("competitor_landscape.html.j2").render(**ctx)

def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_CompetitorLandscape_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8")
    print(f"[CompetitorLandscape] Report saved -> {p.name}"); return str(p)

def _email(email, owner, html_bytes, meta, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    params = {
        "from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email],
        "subject": f"Your Competitor & Market Landscape Report - {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your Competitor &amp; Market Landscape "
                f"Report for {biz} is attached - the full picture of who you are up against and exactly "
                f"how to beat them.</p><p>- EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_CompetitorLandscape_{_slug(biz)}.html")]}
    # Ride-along data-quality notes for the review-email banner. review_gate reads
    # and strips this internal key before the report reaches the customer.
    if dq_warnings:
        params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[CompetitorLandscape] Report email dispatched.")


def generate_competitor_landscape_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None:
        return ""

    # Data-quality gate (B-1): if the file was too broken to read, produce nothing
    # so the fulfillment_guard path takes over (human finishes it by hand). If it's
    # only messy, carry the warnings into the send for the review-email banner.
    # No numeric/date columns here - the competitor table is all free text, so the
    # row-count and overflow checks carry the signal.
    dq = data_quality.assess(df, numeric_cols=[], date_cols=[],
                             label="Competitor Landscape")
    if dq.hard_fail:
        print(f"[Competitor Landscape] Data-quality hard fail: {dq.reason}")
        return ""

    if not meta.get("Owner Name", "").strip():
        meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email:
        _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta, dq_warnings=dq.warnings)
    print(f"[CompetitorLandscape] Pipeline complete -> {customer_email}")
    return path


def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None:
        return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
