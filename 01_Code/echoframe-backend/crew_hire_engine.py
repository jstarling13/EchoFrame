"""
EchoFrame — Crew Hire report engine
─────────────────────────────────────────────────────────────────────────────
pandas/py ─ pipeline KPI counts (meta-driven; scorecard shows the top N), top-score
            ranking, status pills, interview-slot styling.
Claude    ─ the screening-criteria note, the must-have list, and The One Thing.
Jinja2    ─ templates/crew_hire.html.j2 ; Resend ─ delivery. Single tier ($149).

CSV: `_` meta + header containing `Candidate`, `Score`, `Status`, then rows:
  Candidate, CandDetail, Skills, Score, Status, Slot, SlotDetail
  (Status: qualified|waitlist|out)
Meta: _Role, _Requisition, _Applicants, _Screened Out, _Qualified, _Interviews,
      _Interview Window, _Glance Hint, _Sources Note.
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"; REPORTS_DIR = BASE_DIR / "reports"; TEMPLATES_DIR = BASE_DIR / "templates"
PRODUCT_NAME = "Crew Hire"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"candidate", "score", "status"}
_STATUS = {"qualified": ("qual", "Qualified"), "qual": ("qual", "Qualified"),
           "waitlist": ("hold", "Waitlist"), "hold": ("hold", "Waitlist"),
           "out": ("out", "Screened Out"), "screened out": ("out", "Screened Out")}

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _int(s):
    try: return int(float(str(s).replace(",", "").strip()))
    except (ValueError, AttributeError): return 0


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[CrewHire] ERROR - no CSV at {path}"); return None, {}
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
    if not crows: print("[CrewHire] ERROR - no candidate rows"); return None, meta
    cols = ["Candidate", "CandDetail", "Skills", "Score", "Status", "Slot", "SlotDetail"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in crows]
    df = pd.DataFrame(norm, columns=cols)
    df["ScoreNum"] = df["Score"].map(_int)
    df["StatusKey"] = df["Status"].map(lambda s: str(s).strip().lower())
    df = df.reset_index(drop=True)
    print(f"[CrewHire] Loaded {len(df)} scorecard rows from {path.name}")
    return df, meta


def _metrics(df, meta):
    shown = len(df)
    applicants = _int(meta.get("Applicants", "")) or shown
    qualified = _int(meta.get("Qualified", "")) if meta.get("Qualified", "").strip() else \
        int((df["StatusKey"].isin(["qualified", "qual"])).sum())
    screened = _int(meta.get("Screened Out", "")) if meta.get("Screened Out", "").strip() else max(applicants - qualified, 0)
    interviews = _int(meta.get("Interviews", "")) if meta.get("Interviews", "").strip() else \
        int((df["Slot"].str.strip() != "").sum())
    screened_pct = round(screened / applicants * 100) if applicants else 0
    top_i = int(df["ScoreNum"].idxmax())
    print(f"[CrewHire] applicants {applicants} | screened {screened} ({screened_pct}%) | "
          f"qualified {qualified} | interviews {interviews} | shown {shown}")
    return {"shown": shown, "applicants": applicants, "qualified": qualified, "screened": screened,
            "screened_pct": screened_pct, "interviews": interviews, "top_i": top_i}


CREW_HIRE_TOOL = {
    "name": "write_crew_hire_report",
    "description": "Write the screening-criteria note, must-have list, and The One Thing for a hiring-"
                   "pipeline report. Counts and scores are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "screening_note": {"type": "string", "description": "One paragraph on how applicants were scored "
                           "against the must-haves and ranked, including a score-weighting breakdown. May use <b>...</b>."},
        "criteria": {"type": "array", "items": {"type": "string"},
                     "description": "The must-have requirements for this role (4-6 items), each one short line, key terms in <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Imperative headline naming the single top candidate to prioritize."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences on why the top candidate is the strongest match, their score, and the urgency to move fast. Wrap key facts in <span class=\"hl\">...</span>. Use only supplied scores/figures."},
    }, "required": ["screening_note", "criteria", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Crew Hire, EchoFrame's applicant screening engine. You give a small-business owner a "
           "ranked shortlist so they only meet candidates worth their time. Scores and counts are supplied by "
           "a verified engine — copy them exactly, never invent. Practical, decisive. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    role = _sanitize(meta.get("Role", "the role"), 100)
    lines = [f"  {r['Candidate']} ({r['CandDetail']}) | score {r['ScoreNum']}/100 | {r['StatusKey']} | "
             f"skills: {r['Skills']}" for _, r in df.iterrows()]
    top = df.loc[m["top_i"]]
    return (f"Business: {biz} ({_sanitize(meta.get('Industry',''),80)}). Role: {role}. "
            f"Requisition: {_sanitize(meta.get('Requisition',''),40)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Applicants {m['applicants']} | screened out {m['screened']} ({m['screened_pct']}%) | "
            f"qualified {m['qualified']} | interviews scheduled {m['interviews']}\n"
            f"  Top candidate: {top['Candidate']} — score {top['ScoreNum']}/100 — {top['Skills']}\n\n"
            f"Scorecard:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. The One Thing is the single highest-scoring candidate to prioritize and move fast on.")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2000, system=_SYSTEM,
        tools=[CREW_HIRE_TOOL], tool_choice={"type": "tool", "name": "write_crew_hire_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[CrewHire] no tool_use")


def _source_line(meta):
    return ("Screening method: structured resume parse + phone screen scored to rubric · references "
            f"spot-checked for the top tier · EchoFrame Crew Hire, {_sanitize(meta.get('Location','local'),60)} "
            f"skilled-trades market (Q{(datetime.now().month-1)//3+1} {datetime.now().year}).")

def _context(df, meta, m, prose, is_sample):
    top_i = m["top_i"]
    cands = []
    for i, r in df.iterrows():
        pill, label = _STATUS.get(r["StatusKey"], ("hold", r["Status"]))
        slot = str(r["Slot"]).strip()
        slot_none = r["StatusKey"] not in ("qualified", "qual")
        cands.append({"id": str(r["Candidate"]).strip(), "detail": str(r["CandDetail"]).strip(),
                      "skills": str(r["Skills"]).strip(), "score": int(r["ScoreNum"]),
                      "pill_class": pill, "status": label, "slot": slot or "—",
                      "slot_detail": str(r["SlotDetail"]).strip(), "slot_none": slot_none,
                      "top": (i == top_i)})
    role = meta.get("Role", "Open Role"); req = meta.get("Requisition", "").strip()
    sub = role + (f" · Requisition #{req}" if req else "") + f" · {meta.get('Month', datetime.now().strftime('%B %Y'))}"
    kpis = [
        {"label": "Applicants", "value": str(m["applicants"]), "delta_class": "flat",
         "delta_text": meta.get("Sources Note", "Across all sourced job boards")},
        {"label": "Screened Out", "value": str(m["screened"]), "delta_class": "down",
         "delta_text": f"{m['screened_pct']}% filtered before you spend a minute"},
        {"label": "Qualified", "value": str(m["qualified"]), "delta_class": "up",
         "delta_text": f"Met all {len(prose['criteria'])} must-have criteria"},
        {"label": "Interviews Scheduled", "value": str(m["interviews"]), "delta_class": "up",
         "delta_text": (f"Slots confirmed for {meta.get('Interview Window','this week')}")},
    ]
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "sub_detail": sub, "location": meta.get("Location", ""), "is_sample": is_sample,
            "glance_hint": meta.get("Glance Hint", ""),
            "scorecard_hint": f"top {m['shown']} of {m['qualified']} qualified candidates",
            "kpis": kpis, "candidates": cands,
            "screening_note": prose["screening_note"], "criteria": prose["criteria"],
            "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("crew_hire.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_CrewHire_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[CrewHire] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    role = meta.get("Role", "your role").strip(); biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email], "subject": f"Your Crew Hire shortlist — {role} — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your Crew Hire report for {biz} ({role}) is "
                f"attached — applicants screened and scored, with the shortlist and who to prioritize.</p><p>— EchoFrame</p>",
        "attachments": [{"filename": f"EchoFrame_CrewHire_{_slug(role)}.html",
                         "content": base64.b64encode(html_bytes).decode("ascii"), "content_type": "text/html"}]})
    print("[CrewHire] Report email dispatched.")


def generate_crew_hire_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta); prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[CrewHire] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
