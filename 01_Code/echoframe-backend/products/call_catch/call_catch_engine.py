"""
EchoFrame — Call Catch report engine
─────────────────────────────────────────────────────────────────────────────
pandas  ─ revenue-saved sum, recovered count, KPIs (meta-overridable).
Claude  ─ the featured auto-text thread and The One Thing.
Jinja2  ─ templates/call_catch.html.j2 ; Resend ─ delivery. Single tier ($79).

CSV: `_` meta + header containing `Time`, `Missed Call`, `Outcome`, then rows:
  Time, Number, AutoText, Response, Outcome, Amount   (outcome: won|pend|lost)
Meta: _Missed Calls, _Auto Texts, _Avg Send, _Leads Recovered, _Recovery Pct, _Revenue Saved, _Shown.
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
PRODUCT_NAME = "Call Catch"
PRODUCT_TAGLINE = "Missed-call auto-text recovery"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"time", "autotext", "outcome"}

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _to_float(s):
    return csv_utils.to_amount(s)
def _money(n): return f"${n:,.0f}"
def _int(s): return int(_to_float(s))


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[CallCatch] ERROR - no CSV at {path}"); return None, {}
    rows = csv_utils.read_rows(path.read_bytes())
    meta, lrows, header_row, inlist = {}, [], [], False
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
        lrows.append(cells)
    if not lrows: print("[CallCatch] ERROR - no log rows"); return None, meta
    cols = ["Time", "Number", "AutoText", "Response", "Outcome", "Amount"]
    # Rows with MORE cells than columns are the unquoted-thousands signature:
    # "2,300" splits into "2" + "300", truncation drops the "300", and the amount
    # reads as $2. Count them so the data-quality gate can flag the junk row.
    # Map canonical columns to the ACTUAL header positions, so a reordered or renamed
    # column is read from the right slot, not by blind position (finding D-2).
    idx_map = csv_utils.column_index_map(header_row, cols)
    ncols = len(header_row) or len(cols)
    lrows = [csv_utils.repair_overflow_row(r, ncols) for r in lrows]
    overflow_rows = sum(1 for r in lrows if len(r) > ncols)
    norm = [[csv_utils.cell(r, idx_map[k]) for k in range(len(cols))] for r in lrows]
    df = pd.DataFrame(norm, columns=cols)
    df["AmountNum"] = df["Amount"].map(_to_float)
    df["OutKey"] = df["Outcome"].map(lambda s: str(s).strip().lower())
    df = df.reset_index(drop=True)
    df.attrs["dq_rows_in"] = len(lrows)
    df.attrs["dq_overflow_rows"] = overflow_rows
    print(f"[CallCatch] Loaded {len(df)} log rows from {path.name}")
    return df, meta


def _metrics(df, meta):
    # B-2: each headline number can be COMPUTED from the upload, but the customer
    # may also TYPE one at intake. We keep the typed value (the export can be
    # partial) yet record which figures were customer-reported (for the report's
    # provenance footnote) and flag any that the data materially contradicts (for
    # the owner's review email). `missed`/`auto` aren't observable from a call log,
    # so they're inherently customer-reported, not cross-checked.
    reported, disc = [], []
    def _has(k): return bool(meta.get(k, "").strip())

    won_sum = float(df.loc[df["OutKey"] == "won", "AmountNum"].sum())
    data_recovered = int(df["OutKey"].isin(["won", "pend"]).sum())

    if _has("Missed Calls"):
        missed = _int(meta.get("Missed Calls", "")); reported.append("Missed Calls")
    else:
        missed = len(df)
    if _has("Auto Texts"):
        auto = _int(meta.get("Auto Texts", "")); reported.append("Auto-Texts Sent")
    else:
        auto = missed
    avg_send = _sanitize(meta.get("Avg Send", "under 60s"), 20)

    if _has("Leads Recovered"):
        recovered = _int(meta.get("Leads Recovered", "")); reported.append("Leads Recovered")
        n = data_quality.discrepancy_note("Leads Recovered", recovered, data_recovered)
        if n: disc.append(n)
    else:
        recovered = data_recovered

    data_pct = round(recovered / missed * 100) if missed else 0
    if _has("Recovery Pct"):
        rec_pct = _int(meta.get("Recovery Pct", "")); reported.append("Recovery %")
        n = data_quality.discrepancy_note("Recovery %", rec_pct, data_pct)
        if n: disc.append(n)
    else:
        rec_pct = data_pct

    if _to_float(meta.get("Revenue Saved", "")):
        rev_saved = _to_float(meta.get("Revenue Saved", "")); reported.append("Est. Revenue Saved")
        n = data_quality.discrepancy_note("Est. Revenue Saved", rev_saved, won_sum, is_money=True)
        if n: disc.append(n)
    else:
        rev_saved = won_sum

    # E-1: clamp impossible derived figures (can't recover more than were missed; %≤100)
    # and flag an order-of-magnitude revenue overstatement so generate() holds for review.
    recovered = min(recovered, missed) if missed else recovered
    rec_pct = data_quality.clamp_pct(rec_pct, hi=100)  # share ratio (recovered/missed) → ≤100
    severe = data_quality.is_severe_overstatement(rev_saved, won_sum)
    print(f"[CallCatch] missed {missed} | auto {auto} | recovered {recovered} ({rec_pct}%) | saved ${rev_saved:,.0f}")
    return {"missed": missed, "auto": auto, "avg_send": avg_send, "recovered": recovered,
            "rec_pct": rec_pct, "rev_saved": rev_saved, "count": len(df),
            "shown": _int(meta.get("Shown", "")) or len(df),
            "_reported": reported, "_discrepancies": disc, "_severe": severe}


CALL_CATCH_TOOL = {
    "name": "write_call_catch_report",
    "description": "Write the featured auto-text thread and The One Thing for a missed-call recovery "
                   "report. Dollar/count figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "thread_meta": {"type": "string", "description": "One line: 'Thread · <date/time> · Caller <masked number>'."},
        "missed_note": {"type": "string", "description": "Short system note, e.g. '✕ Missed call — no answer (line busy on another job)'."},
        "booked_note": {"type": "string", "description": "Short closing system note, e.g. '✓ Booked — $740 water-heater replacement'."},
        "bubbles": {"type": "array", "items": {"type": "object", "properties": {
            "dir": {"type": "string", "enum": ["out", "in"], "description": "out=from the business, in=from caller."},
            "who": {"type": "string", "description": "Sender label (business name or 'Caller')."},
            "auto": {"type": "string", "description": "Optional auto-tag for the first business text, e.g. 'AUTO · 2:15 PM'. Empty otherwise."},
            "text": {"type": "string", "description": "The message text."},
            "time": {"type": "string", "description": "Delivery/timestamp label, e.g. 'Delivered · 2:15 PM' or '2:16 PM'."}},
            "required": ["dir", "who", "text", "time"]},
            "description": "5-6 alternating bubbles showing a realistic missed-call-to-booked conversation for this industry."},
        "one_thing_title": {"type": "string", "description": "Headline stating the recovery rate and dollars recovered this month."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences on the month's missed calls, recoveries, revenue saved, and where recoveries came from. Wrap key figures in <span class=\"dollar\">...</span>. Use supplied numbers."},
    }, "required": ["thread_meta", "missed_note", "booked_note", "bubbles", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Call Catch, EchoFrame's missed-call recovery engine. You text back missed callers in "
           "under a minute and turn them into booked jobs. Count/dollar figures are supplied by a verified "
           "engine — copy them exactly, never invent. Warm, human, never robotic. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    won = df[df["OutKey"] == "won"].sort_values("AmountNum", ascending=False)
    feat = won.iloc[0] if len(won) else df.iloc[0]
    lines = [f"  {r['Time']} | {r['Number']} | resp: {r['Response']} | {r['OutKey']} {_money(r['AmountNum']) if r['AmountNum'] else ''}"
             for _, r in df.iterrows()]
    return (f"Business: {biz} ({_sanitize(meta.get('Industry',''),80)}). Month: {_sanitize(meta.get('Month',''),30)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Missed calls: {m['missed']} | auto-texts: {m['auto']} | avg send {m['avg_send']}\n"
            f"  Leads recovered: {m['recovered']} ({m['rec_pct']}% of missed calls)\n"
            f"  Est. revenue saved: {_money(m['rev_saved'])}\n"
            f"  Feature this recovery in the thread: {feat['Number']} — {feat['Response']} — {_money(feat['AmountNum'])}\n\n"
            f"Recovered-leads log:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. Build the thread from the featured recovery above.")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2200, system=_SYSTEM,
        tools=[CALL_CATCH_TOOL], tool_choice={"type": "tool", "name": "write_call_catch_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[CallCatch] no tool_use")


def _outcome_label(outkey, amount):
    if outkey == "won":  return ("won", f"Booked · {_money(amount)}")
    if outkey == "pend": return ("pend", "Quoted · pending")
    return ("lost", "No response")

def _context(df, meta, m, prose, is_sample):
    log = []
    for _, r in df.iterrows():
        pill, label = _outcome_label(r["OutKey"], r["AmountNum"])
        log.append({"time": str(r["Time"]), "number": str(r["Number"]),
                    "autotext": str(r["AutoText"]), "response": str(r["Response"]),
                    "outcome": label, "pill_class": pill, "win": (r["OutKey"] == "won")})
    kpis = [
        {"label": "Missed Calls", "value": str(m["missed"]), "unit": "",
         "delta_class": "flat", "delta_text": "Unanswered, busy &amp; after-hours"},
        {"label": "Auto-Texts Sent", "value": str(m["auto"]), "unit": "",
         "delta_class": "up", "delta_text": f"100% caught · avg {m['avg_send']} to send"},
        {"label": "Leads Recovered", "value": str(m["recovered"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {m['rec_pct']}% of missed calls re-engaged"},
        {"label": "Est. Revenue Saved", "value": _money(m["rev_saved"]), "unit": "",
         "delta_class": "up", "delta_text": "Booked jobs that would've walked"},
    ]
    thread = {"meta": prose["thread_meta"], "missed_note": prose["missed_note"],
              "booked_note": prose["booked_note"],
              "bubbles": [{"dir": b.get("dir", "out"), "who": b.get("who", ""),
                           "auto": b.get("auto", ""), "text": b.get("text", ""),
                           "time": b.get("time", "")} for b in prose["bubbles"]]}
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample, "kpis": kpis, "thread": thread,
            "log": log, "log_footnote": f"{m['shown']} of {m['recovered']} recoveries shown",
            "reported_fields": m.get("_reported", []),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("call_catch.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_CallCatch_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[CallCatch] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    params = {"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email], "subject": f"Your {month} Call Catch — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Call Catch report for {biz} is "
                f"attached — every missed call, the text that kept the lead warm, and the revenue recovered.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_CallCatch_{month.replace(' ','_')}.html")]}
    # Ride-along data-quality notes for the review-email banner. review_gate reads
    # and strips this internal key before the report reaches the customer.
    if dq_warnings: params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[CallCatch] Report email dispatched.")


def generate_call_catch_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    # Data-quality gate (B-1): KPIs come from _meta rows, so the value here is
    # catching JUNK data rows (overflow / dropped) that would render as fake call
    # entries — not validating a KPI. numeric_cols=[]: "Amount" is only filled on
    # 'won' rows, so it's legitimately mostly-zero on clean data. date_cols=[]:
    # "Time" holds clock times ("2:15 PM"), not calendar dates — no real date col.
    dq = data_quality.assess(df, numeric_cols=[], date_cols=[], label="Call Catch")
    if dq.hard_fail:
        print(f"[Call Catch] Data-quality hard fail: {dq.reason}")
        return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    if m.get("_severe"):  # E-1: typed figure dwarfs the data by ≥10× — hard hold, owner does it by hand
        print("[Call Catch] Severe typed-vs-data overstatement — routing to manual review."); return ""
    prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    warnings = list(dq.warnings) + list(m.get("_discrepancies", []))  # B-1 gate + B-2 cross-check
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta, dq_warnings=warnings)
    print(f"[CallCatch] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
