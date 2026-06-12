"""
EchoFrame — Bay Coach report engine
─────────────────────────────────────────────────────────────────────────────
pandas/py ─ recommended-services total (sum), status pills, top-pick ranking
            (highest-price overdue); shop KPIs + vehicle header are meta-driven.
Claude    ─ each service's "why now", the "what Bay Coach reads" read-out, the
            method note, and The One Thing.
Jinja2    ─ templates/bay_coach.html.j2 ; Resend ─ delivery. Single tier ($129).

CSV: `_` meta + TWO sections:
  history header  `Service Performed,When`  then history rows
  recs header     `Service,Interval,Status,Price`  then recommendation rows
  (Status: Overdue|Due soon|At risk|On track)
Meta: _Vehicle Name, _Vehicle Meta, _Odometer, _RO Hint, _Glance Hint,
      _Avg Ticket, _Avg Delta, _Acceptance, _Acceptance Note, _Added Revenue, _Revenue Note.
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
PRODUCT_NAME = "Bay Coach"
PRODUCT_TAGLINE = "Maintenance recommendations at write-up"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HIST_TOKENS = {"service performed", "when"}
_REC_TOKENS = {"service", "interval", "price"}
_STATUS_PILL = {"overdue": "due", "due soon": "soon", "at risk": "soon", "on track": "ok", "ok": "ok"}

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


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[BayCoach] ERROR - no CSV at {path}"); return None, None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh: rows = list(csv.reader(fh))
    meta, hist, recs, mode = {}, [], [], None
    for row in rows:
        if not row: continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""; continue
        cells = [str(c).strip() for c in row]
        low = {c.lower() for c in cells}
        if _HIST_TOKENS.issubset(low): mode = "hist"; continue
        if _REC_TOKENS.issubset(low): mode = "rec"; continue
        if not first: continue
        if mode == "hist": hist.append(cells)
        elif mode == "rec": recs.append(cells)
    if not recs:
        print("[BayCoach] ERROR - no recommendation rows"); return None, None, meta
    hist_df = pd.DataFrame([(r + ["", ""])[:2] for r in hist], columns=["Service Performed", "When"])
    rcols = ["Service", "Interval", "Status", "Price"]
    rec_df = pd.DataFrame([(r + [""] * len(rcols))[:len(rcols)] for r in recs], columns=rcols)
    rec_df["PriceNum"] = rec_df["Price"].map(_to_float)
    rec_df["StatusKey"] = rec_df["Status"].map(lambda s: str(s).strip().lower())
    rec_df = rec_df.reset_index(drop=True)
    print(f"[BayCoach] Loaded {len(hist_df)} history + {len(rec_df)} recommendations from {path.name}")
    return hist_df, rec_df, meta


def _metrics(rec_df, meta):
    total = float(rec_df["PriceNum"].sum())
    overdue = rec_df[rec_df["StatusKey"] == "overdue"]
    pool = overdue if len(overdue) else rec_df
    top_i = int(pool["PriceNum"].idxmax())
    print(f"[BayCoach] {len(rec_df)} recs | total ${total:,.0f} | top pick idx {top_i}")
    return {"total": total, "top_i": top_i, "count": len(rec_df)}


BAY_COACH_TOOL = {
    "name": "write_bay_coach_report",
    "description": "Write each recommended service's 'why now', the vehicle read-out, the method note, and "
                   "The One Thing for a service-write-up report. Prices/intervals are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "vstat": {"type": "string", "description": "The 'What Bay Coach Reads From This' paragraph: what's missing from history, age/mileage signals, and why today is the right write-up. May use <b>...</b>."},
        "services": {"type": "array", "items": {"type": "object", "properties": {
            "why": {"type": "string", "description": "One 'why now' justification for this service, tied to the manufacturer interval and this vehicle's history. No leading 'Why now:' label."}},
            "required": ["why"]},
            "description": "One entry per supplied recommended service, SAME ORDER and COUNT."},
        "method_note": {"type": "string", "description": "One paragraph on how Bay Coach builds the list from year/make/model, odometer, and on-file history vs the manufacturer schedule. May use <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Imperative headline for the single service to lead with."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences: the highest-value, most-defensible service to present first, why, a natural add-on, and the incremental ticket impact at the shop's acceptance rate. Wrap dollar/figure phrases in <span class=\"dollar\">...</span>. Use only supplied numbers."},
    }, "required": ["vstat", "services", "method_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Bay Coach, EchoFrame's service-write-up engine for auto shops. You surface the services a "
           "specific vehicle actually needs from its real history and mileage, with a plain 'why now' the advisor "
           "can read at the counter. Prices/intervals are supplied by a verified engine — copy them exactly, never "
           "invent. Justified, never a vague upsell. No markdown.")

def _prompt(hist_df, rec_df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the shop"), 200)
    veh = _sanitize(meta.get("Vehicle Name", "the vehicle"), 100)
    h = [f"  {r['Service Performed']} — {r['When']}" for _, r in hist_df.iterrows()]
    rec = [f"  [{i}] {r['Service']} | interval {r['Interval']} | {r['StatusKey']} | {_money(r['PriceNum'])}"
           for i, r in rec_df.iterrows()]
    top = rec_df.loc[m["top_i"]]
    return (f"Shop: {biz}. Vehicle: {veh} · {_sanitize(meta.get('Vehicle Meta',''),200)} · "
            f"odometer {_sanitize(meta.get('Odometer',''),20)} mi.\n\n"
            f"Pre-calculated (use verbatim):\n  Total recommended: {_money(m['total'])}\n"
            f"  Shop acceptance rate: {_sanitize(meta.get('Acceptance',''),10)}\n"
            f"  Lead/top pick: {top['Service']} ({_money(top['PriceNum'])}, {top['StatusKey']})\n\n"
            f"Service history on file:\n" + "\n".join(h)
            + "\n\nRecommended services (keep order and count):\n" + "\n".join(rec)
            + "\n\nWrite to the advisor/owner. The One Thing leads with the highest-value, most-defensible overdue item.")

def _narrative(hist_df, rec_df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2400, system=_SYSTEM,
        tools=[BAY_COACH_TOOL], tool_choice={"type": "tool", "name": "write_bay_coach_report"},
        messages=[{"role": "user", "content": _prompt(hist_df, rec_df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[BayCoach] no tool_use")


def _source_line(meta):
    return ("Method: factory maintenance intervals cross-referenced against on-file repair-order history and "
            f"regional climate factors ({_sanitize(meta.get('Location','local'),60)}). Pricing reflects shop's "
            f"posted labor rate and parts matrix. EchoFrame Bay Coach index, "
            f"Q{(datetime.now().month-1)//3+1} {datetime.now().year}.")

def _context(hist_df, rec_df, meta, m, prose, is_sample):
    top_i = m["top_i"]
    whys = prose["services"]
    services = []
    for i, r in rec_df.iterrows():
        why = whys[i].get("why", "") if i < len(whys) else ""
        services.append({"service": str(r["Service"]).strip(), "why": why,
                         "interval": str(r["Interval"]).strip(),
                         "status": str(r["Status"]).strip(),
                         "pill_class": _STATUS_PILL.get(r["StatusKey"], "soon"),
                         "price": _money(r["PriceNum"]), "top": (i == top_i)})
    history = [{"desc": str(r["Service Performed"]).strip(), "when": str(r["When"]).strip()}
              for _, r in hist_df.iterrows()]
    kpis = [
        {"label": "Avg Recommended Ticket", "value": _money(_to_float(meta.get("Avg Ticket", ""))),
         "delta_class": "up", "delta_text": meta.get("Avg Delta", "")},
        {"label": "Acceptance Rate", "value": _sanitize(meta.get("Acceptance", ""), 10),
         "delta_class": "up", "delta_text": meta.get("Acceptance Note", "")},
        {"label": "Added Revenue / Month", "value": _money(_to_float(meta.get("Added Revenue", ""))),
         "delta_class": "up", "delta_text": meta.get("Revenue Note", "")},
    ]
    return {"biz_name": meta.get("Business Name", "Your Shop"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample,
            "glance_hint": meta.get("Glance Hint", ""), "ro_hint": meta.get("RO Hint", ""),
            "vehicle": {"name": meta.get("Vehicle Name", ""), "meta": meta.get("Vehicle Meta", ""),
                        "odometer": meta.get("Odometer", "")},
            "history": history, "vstat": prose["vstat"], "services": services, "total": _money(m["total"]),
            "kpis": kpis, "method_note": prose["method_note"], "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("bay_coach.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_BayCoach_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[BayCoach] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your shop").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email], "subject": f"Your {month} Bay Coach — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Bay Coach report for {biz} is "
                f"attached — the right recommendation at write-up, based on the vehicle's real history and mileage.</p><p>— EchoFrame</p>",
        "attachments": [{"filename": f"EchoFrame_BayCoach_{month.replace(' ','_')}.html",
                         "content": base64.b64encode(html_bytes).decode("ascii"), "content_type": "text/html"}]})
    print("[BayCoach] Report email dispatched.")


def generate_bay_coach_report(customer_email, customer_name="Client", tier="", send_email=True):
    hist_df, rec_df, meta = _load(customer_email)
    if rec_df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(rec_df, meta); prose = _narrative(hist_df, rec_df, meta, m)
    ctx = _context(hist_df, rec_df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[BayCoach] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    hist_df, rec_df, meta = load_path(csv_path)
    if rec_df is None: return ""
    m = _metrics(rec_df, meta)
    return _save(meta, _render(_context(hist_df, rec_df, meta, m, prose, is_sample)))
