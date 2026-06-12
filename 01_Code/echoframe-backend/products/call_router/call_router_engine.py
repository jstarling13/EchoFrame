"""
EchoFrame — Call Router report engine
─────────────────────────────────────────────────────────────────────────────
pandas  ─ sample-day footer math (calls logged / booked / booked %), qualification
          pills, after-hours-emergency highlighting; weekly KPIs are meta-driven.
Claude  ─ the After-Hours Capture Note paragraphs and The One Thing.
Jinja2  ─ templates/call_router.html.j2 ; Resend ─ delivery. Single tier ($179).

CSV: `_` meta + header containing `Time`, `Need`, `Qualification`, then rows:
  Time, Tag, Need, Detail, Qualification, Routed, RoutedDetail, Outcome, OutcomeType
  (Tag: AFTER-HOURS/LUNCH/blank; Qualification: Emergency/Estimate/Service call/Non-job;
   OutcomeType: book/hold)
Meta: _Calls Answered, _Calls Total, _Prior Answered Pct, _After Hours Captured,
      _Jobs Booked, _Booked Pct, _Techs, _Period, _Sample Day, _Missed.
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
PRODUCT_NAME = "Call Router"
PRODUCT_TAGLINE = "Inbound answering, job qualification & tech routing"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"time", "need", "qualification"}
_QUAL_PILL = {"emergency": "hot", "estimate": "warm", "service call": "std",
              "service": "std", "non-job": "info", "nonjob": "info"}

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _to_float(s):
    try: return float(str(s).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError): return 0.0
def _int(s): return int(_to_float(s))


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[CallRouter] ERROR - no CSV at {path}"); return None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh: rows = list(csv.reader(fh))
    meta, crows, inlist = {}, [], False
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
        crows.append(cells)
    if not crows: print("[CallRouter] ERROR - no call rows"); return None, meta
    cols = ["Time", "Tag", "Need", "Detail", "Qualification", "Routed", "RoutedDetail", "Outcome", "OutcomeType"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in crows]
    df = pd.DataFrame(norm, columns=cols).reset_index(drop=True)
    print(f"[CallRouter] Loaded {len(df)} sample-day calls from {path.name}")
    return df, meta


def _metrics(df, meta):
    logged = len(df)
    booked = int((df["OutcomeType"].str.strip().str.lower() == "book").sum())
    missed = _int(meta.get("Missed", "")) if meta.get("Missed", "").strip() else 0
    booked_pct = round(booked / logged * 100) if logged else 0
    answered = _int(meta.get("Calls Answered", "")) if meta.get("Calls Answered", "").strip() else logged
    total = _int(meta.get("Calls Total", "")) if meta.get("Calls Total", "").strip() else logged
    answered_pct = round(answered / total * 100) if total else 0
    prior_pct = _int(meta.get("Prior Answered Pct", "")) if meta.get("Prior Answered Pct", "").strip() else None
    afterhours = _int(meta.get("After Hours Captured", "")) if meta.get("After Hours Captured", "").strip() else \
        int(df["Tag"].str.upper().str.contains("AFTER", na=False).sum())
    jobs = _int(meta.get("Jobs Booked", "")) if meta.get("Jobs Booked", "").strip() else booked
    jobs_pct = _int(meta.get("Booked Pct", "")) if meta.get("Booked Pct", "").strip() else \
        (round(jobs / answered * 100) if answered else 0)
    print(f"[CallRouter] sample day {logged} logged / {booked} booked ({booked_pct}%) | "
          f"week: answered {answered}/{total} ({answered_pct}%), after-hours {afterhours}, jobs {jobs}")
    return {"logged": logged, "booked": booked, "missed": missed, "booked_pct": booked_pct,
            "answered": answered, "total": total, "answered_pct": answered_pct, "prior_pct": prior_pct,
            "afterhours": afterhours, "jobs": jobs, "jobs_pct": jobs_pct}


CALL_ROUTER_TOOL = {
    "name": "write_call_router_report",
    "description": "Write the After-Hours Capture Note and The One Thing for a 24/7 call-answering / "
                   "routing report. All counts and dollar figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "after_hours_note": {"type": "array", "items": {"type": "string"},
            "description": "Exactly 2 paragraphs: (1) how after-hours calls were answered live and qualified "
                           "by urgency (emergencies → SMS on-call tech; non-urgent → morning call-back list); "
                           "(2) the industry reality that ~1 in 4 calls is after-hours and lost to voicemail. "
                           "May use <b>...</b>. Use supplied counts."},
        "one_thing_title": {"type": "string", "description": "Headline quantifying the after-hours captured work in dollars this period."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences on the after-hours jobs booked, conservative blended value, what would have been lost on voicemail, and the annualized impact. Wrap dollar figures in <span class=\"dollar\">...</span>. Use supplied numbers."},
    }, "required": ["after_hours_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Call Router, EchoFrame's 24/7 inbound-call answering and dispatch engine. You show a "
           "home-services owner the after-hours and overflow calls you captured that would otherwise have "
           "gone to voicemail and a competitor. Counts/dollar figures are supplied by a verified engine — "
           "copy them exactly, never invent. Practical, blunt. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    lines = [f"  {r['Time']} {('['+r['Tag']+']') if str(r['Tag']).strip() else ''} | {r['Need']} | "
             f"{r['Qualification']} | routed: {r['Routed']} | {r['Outcome']}" for _, r in df.iterrows()]
    return (f"Business: {biz} ({_sanitize(meta.get('Industry',''),80)}). Period: {_sanitize(meta.get('Period',''),40)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Calls answered: {m['answered']} of {m['total']} ({m['answered_pct']}%)\n"
            f"  After-hours captured: {m['afterhours']} (0 to voicemail)\n"
            f"  Jobs booked: {m['jobs']} ({m['jobs_pct']}% of answered)\n"
            f"  After-hours value this period: {_sanitize(meta.get('After Hours Value',''),40)}\n"
            f"  After-hours jobs: {_sanitize(meta.get('After Hours Jobs',''),40)}\n"
            f"  Annualized estimate: {_sanitize(meta.get('Annual Estimate',''),40)}\n\n"
            f"Sample-day call log:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. The One Thing is the dollar value of after-hours calls captured.")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2000, system=_SYSTEM,
        tools=[CALL_ROUTER_TOOL], tool_choice={"type": "tool", "name": "write_call_router_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[CallRouter] no tool_use")


def _source_line(meta):
    return (f"Sources: {_sanitize(meta.get('Business Name','client'),120)} call records ({_sanitize(meta.get('Period',''),40)}) · "
            f"EchoFrame Call Router qualification log · home-services after-hours call benchmarks "
            f"(Q{(datetime.now().month-1)//3+1} {datetime.now().year}). Job values are conservative averages.")

def _context(df, meta, m, prose, is_sample):
    calls = []
    for _, r in df.iterrows():
        qual = str(r["Qualification"]).strip()
        tag = str(r["Tag"]).strip()
        is_emerg = qual.lower() == "emergency"
        is_after = "after" in tag.lower()
        calls.append({"time": str(r["Time"]).strip(), "tag": tag, "need": str(r["Need"]).strip(),
                      "detail": str(r["Detail"]).strip(), "qualification": qual,
                      "qual_class": _QUAL_PILL.get(qual.lower(), "info"),
                      "routed": str(r["Routed"]).strip(), "routed_detail": str(r["RoutedDetail"]).strip(),
                      "outcome": str(r["Outcome"]).strip(),
                      "out_class": ("hold" if str(r["OutcomeType"]).strip().lower() == "hold" else "book"),
                      "top": (is_emerg and is_after)})
    answered_delta = f"▲ {m['answered_pct']}% answered live"
    if m["prior_pct"]: answered_delta += f" — vs. ~{m['prior_pct']}% before Call Router"
    kpis = [
        {"label": "Calls Answered", "value": str(m["answered"]), "unit": f"of {m['total']}",
         "delta_class": "up", "delta_text": answered_delta},
        {"label": "After-Hours Calls Captured", "value": str(m["afterhours"]), "unit": "",
         "delta_class": "flat", "delta_text": "Evenings, weekend &amp; lunch — 0 went to voicemail"},
        {"label": "Jobs Booked", "value": str(m["jobs"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {m['jobs_pct']}% of answered calls converted to a scheduled job"},
    ]
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "period": meta.get("Period", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample,
            "glance_hint": meta.get("Glance Hint", f"{meta.get('Techs','')} on rotation").strip(" ·"),
            "kpis": kpis,
            "log_title": f"Call Log — {meta.get('Sample Day', 'Sample Day')}",
            "calls": calls,
            "foot_text": f"Sample day — {m['logged']} calls logged · {m['booked']} jobs booked · {m['missed']} missed",
            "booked_pct": f"{m['booked_pct']}%",
            "after_hours_note": prose["after_hours_note"], "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("call_router.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_CallRouter_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[CallRouter] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    period = meta.get("Period", "").strip(); biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email], "subject": f"Your Call Router report — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your Call Router report for {biz} ({period}) is "
                f"attached — every inbound call answered, qualified, and routed, plus the after-hours work you'd "
                f"have lost to voicemail.</p><p>— EchoFrame</p>",
        "attachments": [{"filename": f"EchoFrame_CallRouter_{period.replace(' ','_').replace(',','')}.html",
                         "content": base64.b64encode(html_bytes).decode("ascii"), "content_type": "text/html"}]})
    print("[CallRouter] Report email dispatched.")


def generate_call_router_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta); prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[CallRouter] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
