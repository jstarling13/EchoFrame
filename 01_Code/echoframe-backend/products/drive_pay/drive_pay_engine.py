"""
EchoFrame — Drive Pay report engine
─────────────────────────────────────────────────────────────────────────────
pandas/py ─ KPIs (meta-driven; log shows top N of all ROs), outcome pills, the
            text-thread item ordering (ready note → bubbles → paid note → last bubble).
Claude    ─ the text-to-pay thread (bubbles + the two system notes) and The One Thing.
Jinja2    ─ templates/drive_pay.html.j2 ; Resend ─ delivery. Single tier ($79).

CSV: `_` meta + header containing `RO Closed`, `Invoice`, `Outcome`, then rows:
  Time, Customer, Vehicle, Invoice, PayLink, Outcome, OutType   (OutType: won|pend|lost)
Meta: _ROs Closed, _Paid Before, _Paid Pct, _Avg Time, _Avg Time Sub, _Collected,
      _Before Pickup, _Shown.
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
PRODUCT_NAME = "Drive Pay"
PRODUCT_TAGLINE = "Text-to-pay collected at pickup"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]'); _DELIM = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"time", "invoice", "outcome"}
_OUT_PILL = {"won": "won", "pend": "pend", "lost": "lost"}

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _sanitize(v, n=300):
    v = _CTRL.sub('', str(v)); v = _DELIM.sub('', v); return v[:n].strip()
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _to_float(s):
    return csv_utils.to_amount(s)
def _money(n): return f"${n:,.0f}"
def _money2(n): return f"${n:,.2f}"
def _int(s): return int(_to_float(s))


def _load(email): return load_path(UPLOADS_DIR / f"{_safe_email(email)}.csv")
def load_path(path):
    path = Path(path)
    if not path.exists(): print(f"[DrivePay] ERROR - no CSV at {path}"); return None, {}
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
    if not lrows: print("[DrivePay] ERROR - no log rows"); return None, meta
    cols = ["Time", "Customer", "Vehicle", "Invoice", "PayLink", "Outcome", "OutType"]
    # Map canonical columns to the ACTUAL header positions, so a reordered or renamed
    # column is read from the right slot, not by blind position (finding D-2).
    idx_map = csv_utils.column_index_map(header_row, cols)
    ncols = len(header_row) or len(cols)
    # Rows with MORE cells than columns are the signature of an unquoted thousands
    # separator: "2,300" splits into "2" + "300", truncation drops the "300", and
    # the amount reads as $2. Count them so the data-quality gate can flag it.
    lrows = [csv_utils.repair_overflow_row(r, ncols) for r in lrows]
    overflow_rows = sum(1 for r in lrows if len(r) > ncols)
    norm = [[csv_utils.cell(r, idx_map[k]) for k in range(len(cols))] for r in lrows]
    df = pd.DataFrame(norm, columns=cols)
    df["InvoiceNum"] = df["Invoice"].map(_to_float)
    df["OutKey"] = df["OutType"].map(lambda s: str(s).strip().lower())
    df = df.reset_index(drop=True)
    # Record how many data rows the parser SAW so the data-quality gate can tell
    # if any were silently dropped or mis-split (e.g. an unquoted "2,300").
    df.attrs["dq_rows_in"] = len(lrows)
    df.attrs["dq_overflow_rows"] = overflow_rows
    print(f"[DrivePay] Loaded {len(df)} log rows from {path.name}")
    return df, meta


def _metrics(df, meta):
    # B-2: each headline number can be COMPUTED from the upload, but the customer
    # may also TYPE one at intake. We keep the typed value (the export can be
    # partial) yet record which figures were customer-reported (for the report's
    # provenance footnote) and flag any that the data materially contradicts (for
    # the owner's review email). `Avg Time to Pay` and `before_pickup` aren't
    # observable from this log (no payment-clear timestamps, no per-RO before/after
    # flag), so they're inherently customer-reported, not cross-checked.
    reported, disc = [], []
    def _has(k): return bool(meta.get(k, "").strip())

    data_ros = len(df)
    data_paid_before = int((df["OutKey"] == "won").sum())
    data_collected = float(df["InvoiceNum"].sum())

    if _has("ROs Closed"):
        ros = _int(meta.get("ROs Closed", "")); reported.append("Repair Orders Closed")
        n = data_quality.discrepancy_note("Repair Orders Closed", ros, data_ros)
        if n: disc.append(n)
    else:
        ros = data_ros

    if _has("Paid Before"):
        paid_before = _int(meta.get("Paid Before", "")); reported.append("Paid Before Pickup")
        n = data_quality.discrepancy_note("Paid Before Pickup", paid_before, data_paid_before)
        if n: disc.append(n)
    else:
        paid_before = data_paid_before

    data_pct = round(data_paid_before / data_ros * 100) if data_ros else 0
    if _has("Paid Pct"):
        paid_pct = _int(meta.get("Paid Pct", "")); reported.append("Paid Before Pickup %")
        n = data_quality.discrepancy_note("Paid Before Pickup %", paid_pct, data_pct)
        if n: disc.append(n)
    else:
        paid_pct = round(paid_before / ros * 100) if ros else 0

    if _has("Collected"):
        collected = _to_float(meta.get("Collected", "")); reported.append("Collected via Drive Pay")
        n = data_quality.discrepancy_note("Collected via Drive Pay", collected, data_collected, is_money=True)
        if n: disc.append(n)
    else:
        collected = data_collected

    before_pickup = _to_float(meta.get("Before Pickup", ""))
    # E-1: clamp impossible derived figures (can't pay before pickup more than ROs; %≤100)
    # and flag an order-of-magnitude collected overstatement so generate() holds for review.
    paid_before = min(paid_before, ros) if ros else paid_before
    paid_pct = data_quality.clamp_pct(paid_pct, hi=100)  # share ratio (paid_before/ros) → ≤100
    severe = data_quality.is_severe_overstatement(collected, data_collected)
    print(f"[DrivePay] ROs {ros} | paid before {paid_before} ({paid_pct}%) | collected ${collected:,.0f}")
    return {"ros": ros, "paid_before": paid_before, "paid_pct": paid_pct, "collected": collected,
            "before_pickup": before_pickup, "shown": _int(meta.get("Shown", "")) or len(df), "count": len(df),
            "_reported": reported, "_discrepancies": disc, "_severe": severe}


DRIVE_PAY_TOOL = {
    "name": "write_drive_pay_report",
    "description": "Write the text-to-pay thread and The One Thing for a pay-at-pickup report. Dollar/count "
                   "figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "thread_meta": {"type": "string", "description": "One line: 'Thread · <date/time> · Customer <masked number>'."},
        "ready_note": {"type": "string", "description": "System note when the RO is marked ready, e.g. 'RO #4471 marked Ready for Pickup — 2018 Chevy Silverado · $842.50'."},
        "paid_note": {"type": "string", "description": "System note confirming payment, e.g. '✓ Paid $842.50 · Visa ••4419 · Apple Pay · 2m 41s after text'."},
        "bubbles": {"type": "array", "items": {"type": "object", "properties": {
            "dir": {"type": "string", "enum": ["out", "in"], "description": "out=from the shop, in=from customer."},
            "who": {"type": "string", "description": "Sender label (shop name or 'Customer')."},
            "auto": {"type": "string", "description": "Optional auto-tag on shop texts, e.g. 'AUTO · 4:38 PM'. Empty otherwise."},
            "text": {"type": "string", "description": "The message text (the first shop text includes the total and a pay link)."},
            "time": {"type": "string", "description": "Delivery/timestamp label."}},
            "required": ["dir", "who", "text", "time"]},
            "description": "3 bubbles: shop pay-link text, customer reply, shop payment-received text. The paid system note is inserted before the final shop text automatically."},
        "one_thing_title": {"type": "string", "description": "Imperative headline for the single setting/change to collect more at pickup."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences on total collected, % before pickup, the unpaid tail, and the recommended setting (e.g. pay-before-release over a threshold). Wrap dollar/percent figures in <span class=\"dollar\">...</span>. Use only supplied numbers."},
    }, "required": ["thread_meta", "ready_note", "paid_note", "bubbles", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are Drive Pay, EchoFrame's text-to-pay engine for auto shops. You fire a pay link the moment a "
           "repair order closes so the customer pays before leaving the lot. Dollar/count figures are supplied by "
           "a verified engine — copy them exactly, never invent. Friendly, frictionless. No markdown.")

def _prompt(df, meta, m):
    biz = _sanitize(meta.get("Business Name", "the shop"), 200)
    feat = df[df["OutKey"] == "won"].iloc[0] if (df["OutKey"] == "won").any() else df.iloc[0]
    lines = [f"  {r['Time']} | {r['Customer']} ({r['Vehicle']}) | {_money2(r['InvoiceNum'])} | {r['PayLink']} | {r['OutKey']}"
             for _, r in df.iterrows()]
    return (f"Business: {biz}. Month: {_sanitize(meta.get('Month',''),30)}.\n\n"
            f"Pre-calculated (use verbatim):\n  Repair orders closed: {m['ros']} | paid before pickup: {m['paid_before']} ({m['paid_pct']}%)\n"
            f"  Collected via Drive Pay: {_money(m['collected'])} ({_money(m['before_pickup'])} before pickup)\n"
            f"  Feature this paid RO in the thread: {feat['Customer']} — {feat['Vehicle']} — {_money2(feat['InvoiceNum'])}\n\n"
            f"Pickup payment log:\n" + "\n".join(lines)
            + "\n\nWrite to the owner. Build the thread from the featured paid RO. The One Thing is the setting "
            "that would collect more at pickup (e.g. pay-before-release over a dollar threshold).")

def _narrative(df, meta, m):
    import anthropic
    c = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = c.messages.create(model="claude-haiku-4-5-20251001", max_tokens=2200, system=_SYSTEM,
        tools=[DRIVE_PAY_TOOL], tool_choice={"type": "tool", "name": "write_drive_pay_report"},
        messages=[{"role": "user", "content": _prompt(df, meta, m)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[DrivePay] no tool_use")


def _build_thread(prose):
    bubbles = prose["bubbles"]
    items = [{"kind": "sysnote", "tone": "ready", "text": prose["ready_note"]}]
    body = [{"kind": "bubble", "dir": b.get("dir", "out"), "who": b.get("who", ""),
             "auto": b.get("auto", ""), "text": b.get("text", ""), "time": b.get("time", "")}
            for b in bubbles]
    if len(body) >= 2:
        items += body[:-1]
        items.append({"kind": "sysnote", "tone": "paid", "text": prose["paid_note"]})
        items.append(body[-1])
    else:
        items += body
        items.append({"kind": "sysnote", "tone": "paid", "text": prose["paid_note"]})
    return {"meta": prose["thread_meta"], "events": items}


def _context(df, meta, m, prose, is_sample):
    log = []
    for _, r in df.iterrows():
        log.append({"time": str(r["Time"]).strip(), "customer": str(r["Customer"]).strip(),
                    "vehicle": str(r["Vehicle"]).strip(), "invoice": _money2(r["InvoiceNum"]),
                    "paylink": str(r["PayLink"]).strip(), "outcome": str(r["Outcome"]).strip(),
                    "pill_class": _OUT_PILL.get(r["OutKey"], "pend"), "win": (r["OutKey"] == "won")})
    kpis = [
        {"label": "Repair Orders Closed", "value": str(m["ros"]), "unit": "",
         "delta_class": "flat", "delta_text": "Pay link auto-sent on every one"},
        {"label": "Paid Before Pickup", "value": str(m["paid_before"]), "unit": "",
         "delta_class": "up", "delta_text": f"▲ {m['paid_pct']}% collected before the car left"},
        {"label": "Avg Time to Pay", "value": _sanitize(meta.get("Avg Time", "—"), 10),
         "unit": _sanitize(meta.get("Avg Time Sub", ""), 10),
         "delta_class": "up", "delta_text": "From text sent to payment cleared"},
        {"label": "Collected via Drive Pay", "value": _money(m["collected"]), "unit": "",
         "delta_class": "up",
         "delta_text": (f"{_money(m['before_pickup'])} of it before pickup" if m["before_pickup"] else "collected this month")},
    ]
    return {"biz_name": meta.get("Business Name", "Your Shop"), "product_name": PRODUCT_NAME,
            "product_tagline": PRODUCT_TAGLINE, "month": meta.get("Month", datetime.now().strftime("%B %Y")),
            "location": meta.get("Location", ""), "is_sample": is_sample,
            "kpis": kpis, "thread": _build_thread(prose), "log": log,
            "log_footnote": f"{m['shown']} of {m['ros']} repair orders shown",
            "reported_fields": m.get("_reported", []),
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("drive_pay.html.j2").render(**ctx)
def _save(meta, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_DrivePay_{_slug(meta.get('Business Name',''))}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[DrivePay] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, meta, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", "").strip(); biz = meta.get("Business Name", "your shop").strip()
    params = {"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email], "subject": f"Your {month} Drive Pay — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Drive Pay report for {biz} is "
                f"attached — text-to-pay sent at every job close, and what you collected at pickup instead of chasing.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_DrivePay_{month.replace(' ','_')}.html")]}
    # Ride-along data-quality notes for the review-email banner. review_gate reads
    # and strips this internal key before the report reaches the customer.
    if dq_warnings: params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[DrivePay] Report email dispatched.")


def generate_drive_pay_report(customer_email, customer_name="Client", tier="", send_email=True):
    df, meta = _load(customer_email)
    if df is None: return ""
    # Data-quality gate (B-1): if the file was too broken to read, produce nothing
    # so the fulfillment_guard path takes over (human finishes it by hand). If it's
    # only messy, carry the warnings into the send for the review-email banner.
    # InvoiceNum is a real money amount (catches "2,300"→"2" and all-zero columns).
    # Time is a clock label (e.g. "4:38 PM"), not a calendar date, so date_cols=[].
    dq = data_quality.assess(df, numeric_cols=["InvoiceNum"], date_cols=[],
                             label="Drive Pay")
    if dq.hard_fail:
        print(f"[Drive Pay] Data-quality hard fail: {dq.reason}")
        return ""
    if not meta.get("Owner Name", "").strip(): meta["Owner Name"] = customer_name.strip() or "Client"
    m = _metrics(df, meta)
    if m.get("_severe"):  # E-1: typed figure dwarfs the data by ≥10× — hard hold, owner does it by hand
        print("[Drive Pay] Severe typed-vs-data overstatement — routing to manual review."); return ""
    prose = _narrative(df, meta, m)
    ctx = _context(df, meta, m, prose, is_sample=False)
    html = _render(ctx); path = _save(meta, html)
    warnings = list(dq.warnings) + list(m.get("_discrepancies", []))  # B-1 gate + B-2 cross-check
    if send_email: _email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta, dq_warnings=warnings)
    print(f"[DrivePay] Pipeline complete -> {customer_email}")
    return path

def render_from_csv(csv_path, prose, is_sample=True):
    df, meta = load_path(csv_path)
    if df is None: return ""
    m = _metrics(df, meta)
    return _save(meta, _render(_context(df, meta, m, prose, is_sample)))
