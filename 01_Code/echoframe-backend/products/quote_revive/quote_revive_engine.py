"""
EchoFrame — Quote Revive report engine
─────────────────────────────────────────────────────────────────────────────
pandas  ─ won-value sum, jobs-closed count, oldest-quote ranking, KPIs (meta-overridable).
Claude  ─ the 3-step follow-up sequence messages, method note, and The One Thing.
Jinja2  ─ templates/quote_revive.html.j2 ; Resend ─ delivery. Single tier ($99).

CSV: `_` meta + header containing `Quote`, `Value`, `Days Cold`, then rows:
  Quote, Detail, Value, Days Cold, Followups, Status   (status: won|warm|active|dead)
Meta: _Open Value, _Cold Count, _Quotes Revived, _Reply Pct, _Jobs Closed,
      _Revenue Reactivated, _Recovered Pct, _Shown.
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
PRODUCT_NAME = "Quote Revive"
PRODUCT_TAGLINE = "Automated follow-up on ghosted quotes & cold leads"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"quote", "value", "days cold"}
_STATUS_PILL = {"won": ("won", "Job closed"), "warm": ("warm", "Replied — warm"),
                "active": ("active", "In sequence"), "dead": ("dead", "Closed — no")}

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _to_float(s):
    try: return float(str(s).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError): return 0.0
def _money(n): return f"${n:,.0f}"
def _int(s): return int(_to_float(s))


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[QuoteRevive] ERROR - no CSV at {path}"); return None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh: rows = list(csv.reader(fh))
    meta, qrows, inlist = {}, [], False
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
        qrows.append(cells)
    if not qrows: print("[QuoteRevive] ERROR - no quote rows"); return None, meta
    cols = ["Quote", "Detail", "Value", "Days Cold", "Followups", "Status"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in qrows]
    df = pd.DataFrame(norm, columns=cols)
    df["ValueNum"] = df["Value"].map(_to_float); df["DaysNum"] = df["Days Cold"].map(_int)
    df["StatusKey"] = df["Status"].map(lambda s: str(s).strip().lower())
    df = df.reset_index(drop=True)
    print(f"[QuoteRevive] Loaded {len(df)} quotes from {path.name}")
    return df, meta


def _metrics(df, meta):
    won_value = float(df.loc[df["StatusKey"] == "won", "ValueNum"].sum())
    jobs_closed = int((df["StatusKey"] == "won").sum())
    open_value = _to_float(meta.get("Open Value", "")) or float(df["ValueNum"].sum())
    cold_count = _int(meta.get("Cold Count", "")) if meta.get("Cold Count", "").strip() else len(df)
    revived = _int(meta.get("Quotes Revived", "")) if meta.get("Quotes Revived", "").strip() else \
        int(df["StatusKey"].isin(["won", "warm"]).sum())
    reply_pct = _int(meta.get("Reply Pct", "")) if meta.get("Reply Pct", "").strip() else \
        (round(revived / cold_count * 100) if cold_count else 0)
    rev_react = _to_float(meta.get("Revenue Reactivated", "")) or won_value
    jobs = _int(meta.get("Jobs Closed", "")) if meta.get("Jobs Closed", "").strip() else jobs_closed
    recovered_pct = _int(meta.get("Recovered Pct", "")) if meta.get("Recovered Pct", "").strip() else \
        (round(rev_react / open_value * 100) if open_value else 0)
    # Highlight the oldest LIVE quote (dead quotes never get the top spotlight).
    live = df[df["StatusKey"] != "dead"]
    top_i = int((live if len(live) else df)["DaysNum"].idxmax())
    # The One Thing targets the largest-value engaged-but-unclosed quote (active/warm).
    engaged = df[df["StatusKey"].isin(["active", "warm"])]
    one_thing_i = int((engaged if len(engaged) else (live if len(live) else df))["ValueNum"].idxmax())
    print(f"[QuoteRevive] {len(df)} quotes | revived {revived}/{cold_count} | closed {jobs} | "
          f"reactivated ${rev_react:,.0f} ({recovered_pct}%)")
    return {"won_value": won_value, "open_value": open_value, "cold_count": cold_count,
            "revived": revived, "reply_pct": reply_pct, "rev_react": rev_react, "jobs": jobs,
            "recovered_pct": recovered_pct, "top_i": top_i, "one_thing_i": one_thing_i,
            "count": len(df), "shown": _int(meta.get("Shown", "")) or len(df)}


QUOTE_REVIVE_TOOL = {
    "name": "write_quote_revive_report",
    "description": "Write the 3-step follow-up sequence, method note, and One Thing for a quote-"
                   "reactivation report. Dollar figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "steps": {"type": "array", "items": {"type": "object", "properties": {
            "message": {"type": "string", "description": "The example follow-up message for this step, personalized with a customer first name and a real quote/amount from the data. Wrap key phrases (price lock, offer, the 'later' option) in <span class=\"q\">...</span>."},
            "goal": {"type": "string", "description": "Short goal of this step, e.g. 'confirm receipt, stay warm, low pressure'."}},
            "required": ["message", "goal"]},
            "description": "Exactly 3 steps: Day 2 text (confirm receipt), Day 7 email (urgency + social proof), Day 14 text+email (the 'breakup' forcing yes/no/later)."},
        "method_note": {"type": "string", "description": "One paragraph on how the 3-touch sequence works and what Days Cold means. May use <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Imperative headline naming the single biggest live opportunity quote to call personally."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences: the largest engaged-but-unclosed quote, its value, days cold, why it needs a personal call, and the upside. Wrap dollars in <span class=\"dollar\">...</span>."},
    }, "required": ["steps", "method_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Quote Revive, EchoFrame's quote-follow-up engine. You reactivate ghosted quotes "
           "without burning the relationship. Dollar figures are supplied by a verified engine — copy "
           "them exactly, never invent. Persistent but professional. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    lines = [f"  {r['Quote']} ({r['Detail']}) | {_money(r['ValueNum'])} | {r['DaysNum']} days cold | "
             f"{r['Followups']} | status={r['StatusKey']}" for _, r in df.iterrows()]
    top = df.loc[m["one_thing_i"]]
    return (f"Business: {biz} ({_sanitize(meta.get('Industry',''),80)}). Month: {_sanitize(meta.get('Month',''),30)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Open quote value: {_money(m['open_value'])} ({m['cold_count']} cold quotes)\n"
            f"  Quotes revived: {m['revived']}/{m['cold_count']} ({m['reply_pct']}% replied)\n"
            f"  Jobs closed: {m['jobs']} · revenue reactivated {_money(m['rev_react'])} ({m['recovered_pct']}% of cold pipeline)\n"
            f"  Largest live opportunity: {top['Quote']} {_money(top['ValueNum'])} at {top['DaysNum']} days cold (status {top['StatusKey']})\n\n"
            f"Quotes:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. The One Thing is the largest engaged-but-unclosed quote worth a personal call.")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2200, system=_SYSTEM,
        tools=[QUOTE_REVIVE_TOOL], tool_choice={"type": "tool", "name": "write_quote_revive_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[QuoteRevive] no tool_use")


def _source_line(meta):
    return (f"Sources: {_sanitize(meta.get('Business Name','client'),120)} quote log (CSV export) · "
            f"EchoFrame follow-up engine · {_sanitize(meta.get('Industry','industry'),60)} quote-value "
            f"ranges (Q{(datetime.now().month-1)//3+1} {datetime.now().year}). Illustrative figures.")

def _context(df, meta, m, prose, is_sample):
    top_i = m["top_i"]
    # Oldest first, but dead/closed quotes always sink to the bottom.
    order = sorted(df.index, key=lambda i: (df.loc[i, "StatusKey"] == "dead", -df.loc[i, "DaysNum"]))
    quotes = []
    for i in order:
        r = df.loc[i]; pill, label = _STATUS_PILL.get(r["StatusKey"], ("active", r["Status"]))
        quotes.append({"title": str(r["Quote"]), "detail": str(r["Detail"]).strip(),
                       "value": _money(r["ValueNum"]), "days": r["DaysNum"],
                       "followups": str(r["Followups"]).strip(), "pill_class": pill,
                       "status_label": label, "top": (i == top_i)})
    kpis = [
        {"label": "Open Quote Value", "value": _money(m["open_value"]), "unit": "",
         "delta_class": "flat", "delta_text": f"{m['cold_count']} quotes 30+ days cold at month start"},
        {"label": "Quotes Revived", "value": str(m["revived"]), "unit": f"/{m['cold_count']}",
         "delta_class": "up", "delta_text": f"▲ {m['reply_pct']}% replied after follow-up"},
        {"label": "Jobs Closed", "value": str(m["jobs"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {_money(m['rev_react'])} in signed work"},
        {"label": "Revenue Reactivated", "value": _money(m["rev_react"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {m['recovered_pct']}% of cold pipeline recovered"},
    ]
    chans = [("Day 2", "Text"), ("Day 7", "Email"), ("Day 14", "Text + Email")]
    steps = []
    for n, st in enumerate(prose["steps"][:3]):
        steps.append({"day": chans[n][0], "channel": chans[n][1],
                      "message": st.get("message", ""), "goal": st.get("goal", "")})
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample,
            "period_label": f"trailing 30 days · {m['cold_count']} aged quotes worked",
            "kpis": kpis, "steps": steps, "quotes": quotes,
            "worklist_footnote": f"{m['shown']} of {m['cold_count']} shown · {_money(m['open_value'])} open at month start",
            "won_value": _money(m["rev_react"]), "recovered_pct": f"{m['recovered_pct']}%",
            "method_note": prose["method_note"], "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("quote_revive.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_QuoteRevive_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[QuoteRevive] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email], "subject": f"Your {month} Quote Revive — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Quote Revive report for {biz} is "
                f"attached — your ghosted quotes, the follow-ups that reopened them, and the one to call.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_QuoteRevive_{month.replace(' ','_')}.html")]})
    print("[QuoteRevive] Report email dispatched.")


def generate_quote_revive_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta); prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[QuoteRevive] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
