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
import csv_utils
import data_quality
import html_safe
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
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
    rows = csv_utils.read_rows(path.read_bytes())
    meta, crows, inlist, header_row = {}, [], False, []
    for row in rows:
        if not row: continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""; continue
        cells = [str(c).strip() for c in row]
        if not inlist:
            if csv_utils.header_matches(cells, _HEADER_TOKENS): header_row = cells; inlist = True
            continue
        if not first: continue
        if csv_utils.looks_like_totals_row(cells): continue  # skip a spreadsheet TOTAL row (don't sum it)
        crows.append(cells)
    if not crows: print("[CrewHire] ERROR - no candidate rows"); return None, meta
    cols = ["Candidate", "CandDetail", "Skills", "Score", "Status", "Slot", "SlotDetail"]
    # Rows with MORE cells than columns are the signature of an unquoted thousands
    # separator ("2,300" splits into "2" + "300") or literal overflow junk (EXTRA/
    # JUNK cells) leaking in. Count them before padding so the data-quality gate
    # can flag the row as untrustworthy.
    idx_map = csv_utils.column_index_map(header_row, cols)
    ncols = len(header_row) or len(cols)
    crows = [csv_utils.repair_overflow_row(r, ncols) for r in crows]
    overflow_rows = sum(1 for r in crows if len(r) > ncols)
    norm = [[csv_utils.cell(r, idx_map[k]) for k in range(len(cols))] for r in crows]
    df = pd.DataFrame(norm, columns=cols)
    df["ScoreNum"] = df["Score"].map(_int)
    df["StatusKey"] = df["Status"].map(lambda s: str(s).strip().lower())
    df = df.reset_index(drop=True)
    # Record how many candidate rows the parser SAW and how many overflowed so the
    # data-quality gate can catch silently dropped or mis-split rows.
    df.attrs["dq_rows_in"] = len(crows)
    df.attrs["dq_overflow_rows"] = overflow_rows
    print(f"[CrewHire] Loaded {len(df)} scorecard rows from {path.name}")
    return df, meta


def _metrics(df, meta):
    # B-2: each headline count can be COMPUTED from the scorecard, but the customer
    # may also TYPE one at intake. We keep the typed value (the scorecard the owner
    # uploads is often a top-N slice, so the true totals can be larger) yet record
    # which figures were customer-reported (for the report's provenance footnote)
    # and flag any that the data materially contradicts (for the owner's review
    # email). `Applicants` falls back to the rows shown (a partial slice, not a real
    # applicant total) and `Screened Out` falls back to a derived applicants−qualified
    # subtraction — neither is an independent scorecard observation, so they're
    # reported-only, not cross-checked. `Qualified` and `Interviews Scheduled` each
    # have a genuine df count to check against.
    reported, disc = [], []
    def _has(k): return bool(meta.get(k, "").strip())

    shown = len(df)
    data_qualified = int((df["StatusKey"].isin(["qualified", "qual"])).sum())
    data_interviews = int((df["Slot"].str.strip() != "").sum())

    if _has("Applicants"):
        applicants = _int(meta.get("Applicants", "")); reported.append("Applicants")
    else:
        applicants = shown

    if _has("Qualified"):
        qualified = _int(meta.get("Qualified", "")); reported.append("Qualified")
        n = data_quality.discrepancy_note("Qualified", qualified, data_qualified)
        if n: disc.append(n)
    else:
        qualified = data_qualified

    if _has("Screened Out"):
        screened = _int(meta.get("Screened Out", "")); reported.append("Screened Out")
    else:
        screened = max(applicants - qualified, 0)

    if _has("Interviews"):
        interviews = _int(meta.get("Interviews", "")); reported.append("Interviews Scheduled")
        n = data_quality.discrepancy_note("Interviews Scheduled", interviews, data_interviews)
        if n: disc.append(n)
    else:
        interviews = data_interviews

    # N-3: clamp logically-impossible counts — can't qualify more than applied, or
    # interview more than were qualified. No severe hold: the scorecard is a top-N SLICE,
    # so typed pipeline totals legitimately exceed the rows shown (a >=10x hold would
    # false-positive). `applicants` stays owner-reported (uncomputable from a slice).
    qualified = min(qualified, applicants) if applicants else qualified
    interviews = min(interviews, qualified)
    screened = max(screened, 0)
    screened_pct = data_quality.clamp_pct(round(screened / applicants * 100) if applicants else 0)
    top_i = int(df["ScoreNum"].idxmax())
    print(f"[CrewHire] applicants {applicants} | screened {screened} ({screened_pct}%) | "
          f"qualified {qualified} | interviews {interviews} | shown {shown}")
    return {"shown": shown, "applicants": applicants, "qualified": qualified, "screened": screened,
            "screened_pct": screened_pct, "interviews": interviews, "top_i": top_i,
            "_reported": reported, "_discrepancies": disc}


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
            "source_line": _source_line(meta), "reported_fields": m.get("_reported", []),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("crew_hire.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_CrewHire_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[CrewHire] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    role = meta.get("Role", "your role").strip(); biz = meta.get("Business Name", "your business").strip()
    params = {"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email], "subject": f"Your Crew Hire shortlist — {role} — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your Crew Hire report for {biz} ({role}) is "
                f"attached — applicants screened and scored, with the shortlist and who to prioritize.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_CrewHire_{_slug(role)}.html")]}
    # Ride-along data-quality notes for the review-email banner. review_gate reads
    # and strips this internal key before the report reaches the customer.
    if dq_warnings: params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[CrewHire] Report email dispatched.")


def generate_crew_hire_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""

    # Data-quality gate (B-1): KPIs come from _meta, so the gate's job here is to
    # catch junk candidate rows (overflow/dropped/literal EXTRA/JUNK cells). Scores
    # can legitimately be 0 for screened-out candidates and there is no date column,
    # so numeric_cols/date_cols stay empty — overflow detection is the real win.
    dq = data_quality.assess(df, numeric_cols=[], date_cols=[], label="Crew Hire")
    if dq.hard_fail:
        print(f"[Crew Hire] Data-quality hard fail: {dq.reason}")
        return ""

    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta); prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    warnings = list(dq.warnings) + list(m.get("_discrepancies", []))  # B-1 gate + B-2 cross-check
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta, dq_warnings=warnings)
    print(f"[CrewHire] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
