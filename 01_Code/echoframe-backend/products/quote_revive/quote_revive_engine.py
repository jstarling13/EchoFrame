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
from datetime import datetime, timezone
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

import csv_utils
import data_quality
import html_safe

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
    return csv_utils.to_amount(s)
def _money(n): return f"${n:,.0f}"
def _int(s): return int(_to_float(s))


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")


# ── Robust real-world CSV mapping ───────────────────────────────────────────────
# Clients export from QuickBooks, Jobber, Housecall Pro, or a spreadsheet they typed
# by hand — the columns are never named the same way twice. We map by meaning, not by
# position, and derive "days cold" from a date column when there's no days column.

def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(s).lower())).strip()

_FIELD_ALIASES = {
    "value":     ["value", "amount", "quote amount", "quote value", "quoted amount", "price",
                  "total", "estimate amount", "estimate value", "job value", "cost", "subtotal",
                  "grand total", "quoted", "amount due", "total amount"],
    "date":      ["date sent", "sent", "date", "quote date", "date quoted", "quoted date", "created",
                  "created date", "date created", "issued", "date issued", "estimate date", "sent date"],
    "days":      ["days cold", "days", "age", "days old", "days since", "aging", "days outstanding", "cold days"],
    "status":    ["status", "stage", "state", "outcome", "result", "disposition"],
    "followups": ["followups", "follow ups", "follow up", "followup", "touches", "contacts",
                  "times contacted", "attempts", "outreach", "num followups", "no of followups"],
    "quote":     ["quote", "quote id", "quote number", "quote no", "id", "ref", "reference",
                  "estimate", "estimate id", "estimate number", "job number", "job no", "invoice", "number"],
    "detail":    ["detail", "details", "description", "job description", "job", "service", "services",
                  "work", "scope", "line item", "item", "project"],
}
_FIELD_ORDER = ["value", "date", "days", "status", "followups", "quote", "detail"]  # specific → broad


def _contains_alias(name, aliases):
    words = name.split()
    for a in aliases:
        aw = a.split()
        if aw and all(w in words for w in aw):
            return True
    return False


def _map_header(cells):
    """Map a candidate header row to field→column-index by meaning. Two passes:
    exact alias match first, then whole-word containment for anything still open."""
    norm = [_norm(c) for c in cells]
    assigned, used = {}, set()
    for field in _FIELD_ORDER:
        for i, name in enumerate(norm):
            if i in used or not name: continue
            if name in _FIELD_ALIASES[field]:
                assigned[field] = i; used.add(i); break
    for field in _FIELD_ORDER:
        if field in assigned: continue
        for i, name in enumerate(norm):
            if i in used or not name: continue
            if _contains_alias(name, _FIELD_ALIASES[field]):
                assigned[field] = i; used.add(i); break
    return assigned


def _detect_header(rows):
    """Find the header row (the first that maps ≥2 fields incl. a value/status/quote)."""
    for i, row in enumerate(rows[:25]):
        m = _map_header(row)
        if len(m) >= 2 and ("value" in m or "status" in m or "quote" in m):
            return i, m
    return -1, {}


_DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y",
                 "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y", "%d-%b-%Y", "%d-%b-%y"]

def _parse_date(s):
    t = str(s).strip()
    if not t: return None
    try:
        return datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    t = re.sub(r"\s+", " ", t.replace(",", " ")).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(t, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _status_key(s):
    """Map any real-world status word to one of: won / warm / active / dead."""
    n = _norm(s)
    if not n: return "active"
    if n in {"no", "n", "x", "lost", "dead"}: return "dead"
    if n in {"yes", "y", "won", "sold"}: return "won"
    if any(w in n for w in ["won", "sold", "accept", "approv", "sign", "book", "schedul",
                            "paid", "complete", "success", "closed won"]): return "won"
    if any(w in n for w in ["lost", "declin", "reject", "cancel", "void", "expire",
                            "not interested", "unqualified", "closed lost"]): return "dead"
    if any(w in n for w in ["warm", "repl", "interest", "hot", "engag", "negoti", "callback"]): return "warm"
    return "active"


# What counts as a "typo" depends entirely on the company's OWN numbers — there is no
# fixed dollar ceiling. A $250k quote is normal for a $2M-scale shop and absurd for one
# that quotes $500 jobs. So we flag a value only when it dwarfs the company's next-largest
# quote by this multiple — i.e. it's detached from the real range by an order of magnitude
# (an extra few zeros, or a 9,999,999,999 sentinel). Tune SUSPECT_MULT to taste.
SUSPECT_MULT = 50

def _flag_suspects(values):
    """Per-value bools marking likely data-entry typos, RELATIVE to the company's own
    quotes — never an absolute dollar amount. A value is suspect only if it exceeds
    SUSPECT_MULT× the next-largest quote. With fewer than 3 quotes there's nothing to
    compare against, so nothing is flagged."""
    pos = sorted(v for v in values if v > 0)
    if len(pos) < 3:
        return [False] * len(values)
    second_largest = pos[-2]                       # the top legitimate comparator
    threshold = SUSPECT_MULT * second_largest
    return [v > threshold for v in values]


def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[QuoteRevive] ERROR - no CSV at {path}"); return None, {}
    rows = csv_utils.read_rows(path.read_bytes())        # any encoding / delimiter / BOM, never raises
    meta, data = csv_utils.split_meta(rows)              # peel the _Key,value meta off the top
    h, mp = _detect_header(data)
    if h < 0:
        print("[QuoteRevive] ERROR - couldn't recognize quote columns"); return None, meta
    qi, di, vi = mp.get("quote"), mp.get("detail"), mp.get("value")
    dyi, dti, fi, si = mp.get("days"), mp.get("date"), mp.get("followups"), mp.get("status")
    ncols = len(data[h]) or 1                              # detected header width = expected columns
    now = datetime.now(timezone.utc)
    recs, overflow_rows, bad_dates = [], 0, 0
    for row in data[h + 1:]:
        if not row or not any((c or "").strip() for c in row): continue
        row = csv_utils.repair_overflow_row(row, ncols)    # re-join unquoted thousands ("2,300"→"2300")
        if len(row) > ncols: overflow_rows += 1            # still over-wide after repair → shifted/junk row
        quote  = csv_utils.cell(row, qi) if qi is not None else ""
        detail = csv_utils.cell(row, di) if di is not None else ""
        value  = csv_utils.to_amount(csv_utils.cell(row, vi)) if vi is not None else 0.0
        if not quote and not detail and value == 0.0: continue        # blank / junk row
        dated = False
        if dyi is not None and csv_utils.cell(row, dyi):              # explicit "days cold" wins
            days = int(csv_utils.to_amount(csv_utils.cell(row, dyi)))
        elif dti is not None and csv_utils.cell(row, dti):            # else derive from a date
            d = _parse_date(csv_utils.cell(row, dti))
            if d is not None: days, dated = max(0, (now - d).days), True
            else: days = 0; bad_dates += 1                 # date present but unreadable → wrongly "fresh"
        else:
            days = 0
        followups = csv_utils.cell(row, fi) if fi is not None else ""
        rawstatus = csv_utils.cell(row, si) if si is not None else ""
        if not quote: quote = detail or "Quote"
        if not detail: detail = quote
        recs.append((quote, detail, float(value), int(days), followups,
                     rawstatus, _status_key(rawstatus), dated))
    if not recs:
        print("[QuoteRevive] ERROR - no quote rows"); return None, meta
    df = pd.DataFrame(recs, columns=["Quote", "Detail", "ValueNum", "DaysNum",
                                     "Followups", "Status", "StatusKey", "Dated"]).reset_index(drop=True)
    # Data-quality gate inputs. We repair unquoted-thousands splits ("2,300"→"2300") per
    # row against the detected header width, then count any row STILL over-wide (shifted/
    # junk) so the gate flags the C-1 case. dq_bad_dates counts mapped-but-unreadable dates
    # (which silently became "0 days cold / fresh") so generate can warn on them.
    df.attrs["dq_rows_in"] = len(recs)
    df.attrs["dq_overflow_rows"] = overflow_rows
    df.attrs["dq_bad_dates"] = bad_dates
    df["Suspect"] = _flag_suspects(list(df["ValueNum"]))
    n_sus = int(df["Suspect"].sum())
    print(f"[QuoteRevive] Loaded {len(df)} quotes from {path.name} (mapped: {sorted(mp)}"
          + (f", {n_sus} flagged as likely typos)" if n_sus else ")"))
    return df, meta


def _metrics(df, meta):
    # B-2: each headline number can be COMPUTED from the upload, but the customer
    # may also TYPE one at intake. We keep the typed value (the export can be
    # partial) yet record which figures were customer-reported (for the report's
    # provenance footnote) and flag any that the data materially contradicts (for
    # the owner's review email). Compute the data value even when a figure is typed
    # — the old `or`/short-circuit form skipped the cross-check on reported figures.
    reported, disc = [], []
    def _has(k): return bool(meta.get(k, "").strip())

    not_suspect = (~df["Suspect"]) if "Suspect" in df.columns else pd.Series(True, index=df.index)
    won_value = float(df.loc[df["StatusKey"] == "won", "ValueNum"].sum())
    jobs_closed = int((df["StatusKey"] == "won").sum())

    data_open_value = float(df.loc[not_suspect, "ValueNum"].sum())
    if _to_float(meta.get("Open Value", "")):
        open_value = _to_float(meta.get("Open Value", "")); reported.append("Open Quote Value")
        n = data_quality.discrepancy_note("Open Quote Value", open_value, data_open_value, is_money=True)
        if n: disc.append(n)
    else:
        open_value = data_open_value

    if _has("Cold Count"):
        cold_count = _int(meta.get("Cold Count", "")); reported.append("Cold Count")
    else:
        cold_count = len(df)

    data_revived = int(df["StatusKey"].isin(["won", "warm"]).sum())
    if _has("Quotes Revived"):
        revived = _int(meta.get("Quotes Revived", "")); reported.append("Quotes Revived")
        n = data_quality.discrepancy_note("Quotes Revived", revived, data_revived)
        if n: disc.append(n)
    else:
        revived = data_revived

    data_reply_pct = round(revived / cold_count * 100) if cold_count else 0
    if _has("Reply Pct"):
        reply_pct = _int(meta.get("Reply Pct", "")); reported.append("Reply %")
        n = data_quality.discrepancy_note("Reply %", reply_pct, data_reply_pct)
        if n: disc.append(n)
    else:
        reply_pct = data_reply_pct

    if _to_float(meta.get("Revenue Reactivated", "")):
        rev_react = _to_float(meta.get("Revenue Reactivated", "")); reported.append("Revenue Reactivated")
        n = data_quality.discrepancy_note("Revenue Reactivated", rev_react, won_value, is_money=True)
        if n: disc.append(n)
    else:
        rev_react = won_value

    if _has("Jobs Closed"):
        jobs = _int(meta.get("Jobs Closed", "")); reported.append("Jobs Closed")
        n = data_quality.discrepancy_note("Jobs Closed", jobs, jobs_closed)
        if n: disc.append(n)
    else:
        jobs = jobs_closed

    data_recovered_pct = round(rev_react / open_value * 100) if open_value else 0
    if _has("Recovered Pct"):
        recovered_pct = _int(meta.get("Recovered Pct", "")); reported.append("Recovered %")
        n = data_quality.discrepancy_note("Recovered %", recovered_pct, data_recovered_pct)
        if n: disc.append(n)
    else:
        recovered_pct = data_recovered_pct
    # E-1: clamp impossible derived figures so a customer-typed number can't print an
    # absurd report (e.g. "40 of 3 revived / 7500% recovered"); flag an order-of-magnitude
    # overstatement so generate() can route it to manual review instead of one-click send.
    revived = min(revived, cold_count)
    jobs = min(jobs, revived)
    reply_pct = data_quality.clamp_pct(reply_pct)                  # share ratio → ≤100
    recovered_pct = data_quality.clamp_pct(recovered_pct, hi=150)  # reactivation can exceed 100
    severe = (data_quality.is_severe_overstatement(open_value, data_open_value)
              or data_quality.is_severe_overstatement(rev_react, won_value))
    # Highlight the oldest LIVE quote (dead quotes never get the top spotlight).
    live = df[df["StatusKey"] != "dead"]
    top_i = int((live if len(live) else df)["DaysNum"].idxmax())
    # The One Thing targets the largest-value engaged-but-unclosed quote (active/warm),
    # skipping any value flagged as a likely typo so a bogus number never headlines.
    engaged = df[df["StatusKey"].isin(["active", "warm"]) & not_suspect]
    fallback = df[not_suspect] if len(df[not_suspect]) else df
    one_thing_i = int((engaged if len(engaged) else (live if len(live) else fallback))["ValueNum"].idxmax())
    print(f"[QuoteRevive] {len(df)} quotes | revived {revived}/{cold_count} | closed {jobs} | "
          f"reactivated ${rev_react:,.0f} ({recovered_pct}%)")
    return {"won_value": won_value, "open_value": open_value, "cold_count": cold_count,
            "revived": revived, "reply_pct": reply_pct, "rev_react": rev_react, "jobs": jobs,
            "recovered_pct": recovered_pct, "top_i": top_i, "one_thing_i": one_thing_i,
            "count": len(df), "shown": _int(meta.get("Shown", "")) or len(df),
            "_reported": reported, "_discrepancies": disc, "_severe": severe}


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
            "reported_fields": m.get("_reported", []),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("quote_revive.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_QuoteRevive_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[QuoteRevive] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    params = {"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email], "subject": f"Your {month} Quote Revive — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Quote Revive report for {biz} is "
                f"attached — your ghosted quotes, the follow-ups that reopened them, and the one to call.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_QuoteRevive_{month.replace(' ','_')}.html")]}
    # Ride-along data-quality notes for the review-email banner. review_gate reads and
    # strips this internal key before the report reaches the customer.
    if dq_warnings: params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[QuoteRevive] Report email dispatched.")


def generate_quote_revive_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    # Data-quality gate (B-1): hard-fail on a file too broken to trust (engine returns ""
    # so fulfillment_guard hands it to a human); carry warnings into the send otherwise.
    # numeric_cols=["ValueNum"]: a file where EVERY quote value is 0/blank is indistinguishable
    # from a value column that didn't read, so it hard-fails. date_cols=[]: dates are consumed
    # into DaysNum (no date column survives on the frame) — instead we warn below from
    # dq_bad_dates, which counts mapped-but-unreadable dates that silently became "0 days cold".
    dq = data_quality.assess(df, numeric_cols=["ValueNum"], date_cols=[], label="Quote Revive")
    if dq.hard_fail:
        print(f"[Quote Revive] Data-quality hard fail: {dq.reason}")
        return ""
    _bad_dates = df.attrs.get("dq_bad_dates", 0)
    if _bad_dates:
        dq.warnings.append(
            f"{_bad_dates} quote(s) had an unreadable date — treated as 0 days cold (fresh). "
            f"Verify their age before chasing.")
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    if m.get("_severe"):  # E-1: typed figure dwarfs the data by ≥10× — hard hold, owner does it by hand
        print("[Quote Revive] Severe typed-vs-data overstatement — routing to manual review.")
        return ""
    prose = _narrative(df, meta, m)
    warnings = list(dq.warnings) + list(m.get("_discrepancies", []))  # B-1 gate + B-2 cross-check
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta, dq_warnings=warnings)
    print(f"[QuoteRevive] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
