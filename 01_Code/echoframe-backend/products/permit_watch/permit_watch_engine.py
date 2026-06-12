"""
EchoFrame — Permit Watch report engine
─────────────────────────────────────────────────────────────────────────────
pandas/py ─ days-until-due (expiry − as-of), status pills, KPI counts, urgency sort.
Claude    ─ the per-deadline alert descriptions, method note, and The One Thing.
Jinja2    ─ templates/permit_watch.html.j2 ; Resend ─ delivery. Single tier ($89).

CSV: `_` meta + header containing `Item`, `Expiry`, then rows:
  Item, ItemDetail, Entity, EntityDetail, Expiry
Meta: _Items Tracked, _As Of, _Fleet Hint, _Foot Extra.
Days/status are computed; an item is Lapsed (<0), Due soon (0–30), On track (>30).
"""

import os, re, csv, base64
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
PRODUCT_NAME = "Permit Watch"
PRODUCT_TAGLINE = "Registration, license & permit tracking with 30-day expiry alerts"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"item", "entity", "expiry"}
_DUE_WINDOW = 30
_DATE_FMTS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y")

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _int(s):
    try: return int(float(str(s).replace(",", "").strip()))
    except (ValueError, AttributeError): return 0
def _parse_date(s):
    s = str(s).strip()
    for f in _DATE_FMTS:
        try: return datetime.strptime(s, f).date()
        except ValueError: continue
    return None
def _short_date(d): return d.strftime("%b ") + str(d.day) if d else ""
def _days_str(n): return f"−{abs(n)}" if n < 0 else str(n)


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[PermitWatch] ERROR - no CSV at {path}"); return None, {}
    with path.open("r", encoding="utf-8-sig", newline="") as fh: rows = list(csv.reader(fh))
    meta, irows, inlist = {}, [], False
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
        irows.append(cells)
    if not irows: print("[PermitWatch] ERROR - no item rows"); return None, meta
    cols = ["Item", "ItemDetail", "Entity", "EntityDetail", "Expiry"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in irows]
    df = pd.DataFrame(norm, columns=cols).reset_index(drop=True)
    print(f"[PermitWatch] Loaded {len(df)} items from {path.name}")
    return df, meta


def _status(days):
    if days < 0: return ("lapsed", "Lapsed", "neg")
    if days <= _DUE_WINDOW: return ("due", "Due soon", "soon")
    return ("ok", "On track", "ok")

def _metrics(df, meta):
    as_of = _parse_date(meta.get("As Of", "")) or datetime.now().date()
    df["ExpiryDate"] = df["Expiry"].map(_parse_date)
    df["Days"] = df["ExpiryDate"].map(lambda d: (d - as_of).days if d else 9999)
    df = df.sort_values("Days", kind="stable").reset_index(drop=True)
    tracked = _int(meta.get("Items Tracked", "")) or len(df)
    expiring = int(((df["Days"] >= 0) & (df["Days"] <= _DUE_WINDOW)).sum())
    lapsed = int((df["Days"] < 0).sum())
    print(f"[PermitWatch] {len(df)} items | tracked {tracked} | expiring<=30 {expiring} | lapsed {lapsed} | as of {as_of}")
    return {"df": df, "as_of": as_of, "tracked": tracked, "expiring": expiring,
            "lapsed": lapsed, "shown": len(df)}


PERMIT_WATCH_TOOL = {
    "name": "write_permit_watch_report",
    "description": "Write the deadline alert descriptions, method note, and The One Thing for a fleet/"
                   "license compliance report. Dates and day-counts are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "alerts": {"type": "array", "items": {"type": "object", "properties": {
            "label": {"type": "string", "description": "Short headline for this deadline, e.g. 'Van #3 registration' or 'USDOT annual update'."},
            "desc": {"type": "string", "description": "One sentence: the concrete renewal action and the consequence of letting it lapse."}},
            "required": ["label", "desc"]},
            "description": "One entry per supplied urgent item, SAME ORDER and COUNT (most urgent first)."},
        "method_note": {"type": "array", "items": {"type": "string"},
            "description": "Exactly 2 paragraphs on how Permit Watch logs each item, alerts at 30/14/3 days, and what Days Until Due means. Use supplied counts. May use <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Imperative headline for the single most urgent compliance item (the lapsed one if any)."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences: the lapsed/most-urgent item, the real exposure (citation, impound, denied insurance claim), the fix today, and that everything else has runway. Wrap key figures/phrases in <span class=\"dollar\">...</span>."},
    }, "required": ["alerts", "method_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Permit Watch, EchoFrame's fleet/license compliance tracker. You flag every registration, "
           "license, insurance policy, and permit before it lapses. Dates and day-counts are supplied by a "
           "verified engine — copy them exactly, never invent. Direct, practical. No markdown.")

def _prompt(df, meta, m, urgent):
    biz = _sanitize(meta.get("Business Name", "the business"), 200)
    ul = [f"  [{i}] {r['Item']} — {r['Entity']} | expires {r['Expiry']} | {_days_str(r['Days'])} days"
          for i, r in urgent.iterrows()]
    return (f"Business: {biz} ({_sanitize(meta.get('Industry',''),80)}). As of {m['as_of']:%b %d, %Y}.\n\n"
            f"Pre-calculated (use verbatim):\n  Items tracked: {m['tracked']} | expiring in 30 days: {m['expiring']} | lapsed: {m['lapsed']}\n\n"
            f"Urgent items (≤30 days or already lapsed, most urgent first):\n" + "\n".join(ul)
            + "\n\nWrite to the owner. One alert entry per urgent item above, same order. The One Thing is the "
            "lapsed/most-urgent item and its real exposure (citation, impound, denied insurance claim).")

def _narrative(df, meta, m, urgent):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2200, system=_SYSTEM,
        tools=[PERMIT_WATCH_TOOL], tool_choice={"type": "tool", "name": "write_permit_watch_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m, urgent)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[PermitWatch] no tool_use")


def _source_line(meta):
    return (f"Source: client-supplied renewal records · GA DRIVES vehicle registration · FMCSA / USDOT filings · "
            f"state licensing board · EchoFrame Permit Watch register ({_sanitize(meta.get('Month',''),20)}).")

def _context(df, meta, m, prose, is_sample):
    d = m["df"]
    rows = []
    for _, r in d.iterrows():
        pill, status, dcls = _status(r["Days"])
        rows.append({"item": str(r["Item"]).strip(), "item_detail": str(r["ItemDetail"]).strip(),
                     "entity": str(r["Entity"]).strip(), "entity_detail": str(r["EntityDetail"]).strip(),
                     "expiry": str(r["Expiry"]).strip(), "days": _days_str(int(r["Days"])),
                     "days_class": dcls, "pill_class": pill, "status": status, "top": (r["Days"] < 0)})
    # urgent = lapsed + due-soon, already sorted by days asc
    urgent = d[d["Days"] <= _DUE_WINDOW]
    descs = prose["alerts"]
    alerts = []
    for n, (_, r) in enumerate(urgent.iterrows()):
        days = int(r["Days"]); short = _short_date(r["ExpiryDate"])
        if days < 0:
            verb, tone, dot = "expired", "", "red"
        elif days <= 14:
            verb, tone, dot = "due", "amber", "amber"
        else:
            verb, tone, dot = "renews", "amber", "amber"
        a = descs[n] if n < len(descs) else {"label": str(r["Item"]), "desc": ""}
        alerts.append({"dot": dot, "label": a.get("label", str(r["Item"])),
                       "when": f"{verb} {short} ({_days_str(days)} days)", "when_tone": tone,
                       "desc": a.get("desc", "")})
    # KPI 3 lapsed delta text
    if m["lapsed"]:
        lr = d[d["Days"] < 0].iloc[0]
        ent_short = str(lr["Entity"]).split("·")[0].strip()
        lapsed_delta = f"▲ {ent_short} tag expired — vehicle is non-compliant now"
    else:
        lapsed_delta = "All items current"
    kpis = [
        {"label": "Items Tracked", "value": str(m["tracked"]), "warn": False, "red": False,
         "delta_class": "flat", "delta_text": "Registrations · licenses · insurance · permits"},
        {"label": "Expiring in 30 Days", "value": str(m["expiring"]), "warn": False, "red": False,
         "delta_class": "down", "delta_text": "▲ Alerts already sent — renew before lapse"},
        {"label": "Lapsed / At Risk", "value": str(m["lapsed"]), "warn": True, "red": True,
         "delta_class": "down", "delta_text": lapsed_delta},
    ]
    foot = f"Showing {m['shown']} of {m['tracked']} tracked items"
    extra = meta.get("Foot Extra", "").strip()
    foot += f" · {extra}" if extra else " · full register available in the client portal."
    return {"biz_name": meta.get("Business Name", "Your Business"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample,
            "fleet_hint": meta.get("Fleet Hint", ""),
            "as_of": f"{m['as_of'].strftime('%b')} {m['as_of'].day}, {m['as_of'].year}",
            "kpis": kpis, "rows": rows, "alerts": alerts, "foot_text": foot,
            "method_note": prose["method_note"], "source_line": _source_line(meta),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    return env.get_template("permit_watch.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_PermitWatch_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[PermitWatch] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your business").strip()
    resend.Emails.send({"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>"),
        "to": [email], "subject": f"Your {month} Permit Watch — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Permit Watch report for {biz} is "
                f"attached — every registration, license, and permit with what's expiring next.</p><p>— EchoFrame</p>",
        "attachments": [{"filename": f"EchoFrame_PermitWatch_{month.replace(' ','_')}.html",
                         "content": base64.b64encode(html_bytes).decode("ascii"), "content_type": "text/html"}]})
    print("[PermitWatch] Report email dispatched.")


def generate_permit_watch_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    urgent = m["df"][m["df"]["Days"] <= _DUE_WINDOW]
    prose = _narrative(df, meta, m, urgent)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[PermitWatch] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
