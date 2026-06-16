"""
EchoFrame — Rate Watch report engine
─────────────────────────────────────────────────────────────────────────────
Same separation of concerns as engine.py / auto_ledger_engine.py:

  pandas   ─ ALL math: total vendor spend, total overpayment, % over market,
             renewal counting inside the tier's alert window, top-gap ranking.
  Claude   ─ ONLY prose + labels via tool_use: each vendor's short Action,
             the Benchmarking Note paragraph, and The One Thing.
  Jinja2   ─ ALL document structure (templates/rate_watch.html.j2).
  Resend   ─ email delivery with the HTML report.

Tiers:
  core ─ up to 10 vendors, renewal alerts 60 days out.
  pro  ─ unlimited vendors, alerts 90 days out, quarterly re-benchmarking note.

CSV format  (uploads/<safe_email>.csv)
─────────────────────────────────────────────────────────────────────────────
Rows whose first cell starts with `_` are metadata. A header row equal to
`Vendor,Detail,Current Rate,Market Rate,Annual Spend,Overpayment,Renewal`
(case-insensitive on the first three tokens) starts the vendor list.

Example:
  _Business Name,Magnolia Lane Salon & Spa LLC
  _Owner Name,Renee
  _Industry,Salon & Spa
  _Location,Columbus GA
  _Month,June 2026
  _Tier,pro
  Vendor,Detail,Current Rate,Market Rate,Annual Spend,Overpayment,Renewal
  Merchant Card Processing,effective rate on ~$46K/mo volume,2.95%,2.45%,16284,3480,2026-07-15
  Commercial Lease,Broadway St. suite,$3200/mo,$2950/mo,38400,3000,2026-09-30
  ...

`Annual Spend` and `Overpayment` are plain numbers (annualized dollars).
`Renewal` is a date (YYYY-MM-DD / Mon D, YYYY) or a label like
"Month-to-month", "Regulated", "Jan 2027".
"""

import os
import re
import csv
import base64
from pathlib import Path
from datetime import datetime

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR      = Path(__file__).resolve().parent
UPLOADS_DIR   = BASE_DIR / "uploads"
REPORTS_DIR   = BASE_DIR / "reports"
TEMPLATES_DIR = BASE_DIR / "templates"

PRODUCT_NAME    = "Rate Watch"
PRODUCT_TAGLINE = "Vendor benchmarking & renewal alerts"

TIER_LABELS  = {"core": "Core", "pro": "Pro"}
TIER_WINDOWS = {"core": 60, "pro": 90}   # renewal-alert horizon in days

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_PROMPT_DELIMITER_RE = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"vendor", "current rate", "market rate"}


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _safe_email(email: str) -> str:
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', local)}_at_{_SAFE_CHAR_RE.sub('_', domain)}"


def _sanitize(value: str, max_len: int = 300) -> str:
    value = _CTRL_CHARS_RE.sub('', str(value))
    value = _PROMPT_DELIMITER_RE.sub('', value)
    return value[:max_len].strip()


def _report_slug(business_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (business_name or "").lower()).strip("_")
    return slug or "report"


def _to_float(s) -> float:
    try:
        return float(str(s).replace("$", "").replace(",", "").replace("%", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _money(n: float) -> str:
    sign = "−" if n < 0 else ""
    return f"{sign}${abs(n):,.0f}"


# ── Step 1: CSV ingestion ───────────────────────────────────────────────────────

def _load_vendors(customer_email: str):
    return load_vendors_path(UPLOADS_DIR / f"{_safe_email(customer_email)}.csv")


def load_vendors_path(path: Path):
    """Parse a vendor CSV into (vendors_df, meta_dict). Public for demo use."""
    path = Path(path)
    if not path.exists():
        print(f"[RateWatch] ERROR - no CSV found at: {path}")
        return None, {}

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))

    meta, vrows, in_list = {}, [], False
    for row in rows:
        if not row:
            continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""
            continue
        cells = [str(c).strip() for c in row]
        if not in_list:
            lowered = {c.lower() for c in cells}
            if _HEADER_TOKENS.issubset(lowered):
                in_list = True
            continue
        if not first:
            continue
        vrows.append(cells)

    if not vrows:
        print("[RateWatch] ERROR - no vendor rows found after header.")
        return None, meta

    cols = ["Vendor", "Detail", "Current Rate", "Market Rate", "Annual Spend", "Overpayment", "Renewal"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in vrows]
    df = pd.DataFrame(norm, columns=cols)
    df["Annual Spend"] = df["Annual Spend"].map(_to_float)
    df["Overpayment"]  = df["Overpayment"].map(_to_float)
    df = df.reset_index(drop=True)
    print(f"[RateWatch] Loaded {len(df)} vendors from {path.name}")
    return df, meta


# ── Step 2: all math in pandas ──────────────────────────────────────────────────

_DATE_FMTS = ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%b %Y", "%B %Y", "%Y")


def _parse_renewal(s: str):
    s = str(s).strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _fmt_renewal(s: str) -> str:
    """Pretty-print parseable full dates; pass labels through unchanged."""
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%b %d, %Y")
        except ValueError:
            continue
    return s


def _reference_date(meta: dict):
    """The 'today' the renewal window is measured from — first of the report month."""
    d = _parse_renewal(meta.get("Month", ""))
    return d or datetime.now().date()


def _calculate_metrics(df: pd.DataFrame, meta: dict, window_days: int) -> dict:
    total_spend = float(df["Annual Spend"].sum())
    total_over  = float(df["Overpayment"].sum())
    over_pct    = (total_over / total_spend * 100) if total_spend > 0 else 0.0
    over_count  = int((df["Overpayment"] > 0).sum())

    ref = _reference_date(meta)
    upcoming = []
    for _, r in df.iterrows():
        d = _parse_renewal(r["Renewal"])
        if d and 0 <= (d - ref).days <= window_days:
            upcoming.append(d)
    upcoming.sort()
    renewal_dates = " · ".join(d.strftime("%b %-d" if os.name != "nt" else "%b %#d") + f", {d.year}"
                               for d in upcoming) if upcoming else "None in window"

    # Rank: largest overpayment is "the one thing" / top row.
    # Stable sort so tied gaps keep their input order.
    order = df["Overpayment"].sort_values(ascending=False, kind="stable").index.tolist()

    print(f"[RateWatch] Spend ${total_spend:,.0f}/yr | Overpayment ${total_over:,.0f}/yr "
          f"({over_pct:.1f}%) | {over_count}/{len(df)} over market | "
          f"{len(upcoming)} renewals in {window_days}d")

    return {
        "total_spend": total_spend, "total_over": total_over,
        "over_pct": over_pct, "over_count": over_count,
        "vendor_count": len(df),
        "renewal_count": len(upcoming), "renewal_dates": renewal_dates,
        "order": order, "top_index": order[0] if order else None,
        "window_days": window_days,
    }


# ── Step 3: Claude via tool_use — actions + prose only ──────────────────────────

RATE_WATCH_TOOL = {
    "name": "write_rate_watch_report",
    "description": (
        "Recommend a short next-step Action for each vendor and write the report "
        "narrative. All dollar figures are pre-calculated and supplied — never invent "
        "or alter a number. Return prose only: no markdown, no tables."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vendors": {
                "type": "array",
                "description": "One entry per supplied vendor, SAME ORDER and COUNT.",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "0-based index as supplied."},
                        "action": {"type": "string", "description": "2-4 word imperative next step, e.g. 'Renegotiate now', 'Re-shop policy', 'Downgrade tier', 'Re-bid at renewal', 'Switch plan', 'Monitor usage', 'Hold'. Use 'Hold' for at-market vendors."},
                    },
                    "required": ["index", "action"],
                },
            },
            "benchmarking_note": {
                "type": "string",
                "description": "One paragraph (~70-90 words) explaining how vendors were benchmarked against the local market, what Over/Under means (annualized gap, a starting point not a guarantee), how many of N are above market, and where the recoverable spread is concentrated. May wrap a phrase in <b>...</b>.",
            },
            "one_thing_title": {"type": "string", "description": "Imperative headline naming the single highest-gap vendor and its renewal timing."},
            "one_thing_body": {"type": "string", "description": "3-4 sentences: why this is the largest gap, the current vs market rate, the annual dollars, the renewal leverage, and the concrete ask. Wrap dollar/rate figures in <span class=\"dollar\">...</span>. Use only supplied numbers."},
        },
        "required": ["vendors", "benchmarking_note", "one_thing_title", "one_thing_body"],
    },
}


def _build_prompt(df, meta, metrics):
    biz      = _sanitize(meta.get("Business Name", "the business"), 200)
    industry = _sanitize(meta.get("Industry", "small business"), 100)
    location = _sanitize(meta.get("Location", ""), 150)
    month    = _sanitize(meta.get("Month", ""), 30)

    lines = []
    for i, r in df.iterrows():
        op = float(r["Overpayment"])
        status = f"+{_money(op)}/yr over market" if op > 0 else "at market"
        lines.append(
            f"  [{i}] {r['Vendor']}"
            + (f" ({r['Detail']})" if str(r['Detail']).strip() else "")
            + f" | current {r['Current Rate']} vs market {r['Market Rate']} | {status}"
            + f" | renewal {r['Renewal']}"
        )

    top = metrics["top_index"]
    top_line = (f"\nHighest-gap vendor = [{top}] {df.loc[top, 'Vendor']} "
                f"(+{_money(df.loc[top, 'Overpayment'])}/yr).") if top is not None else ""

    return (
        f"Business: {biz} ({industry}{', ' + location if location else ''}). Month: {month}.\n\n"
        f"Pre-calculated figures (use verbatim, never recompute):\n"
        f"  Total vendor spend: {_money(metrics['total_spend'])}/yr\n"
        f"  Estimated overpayment: {_money(metrics['total_over'])}/yr "
        f"({metrics['over_pct']:.1f}% of spend)\n"
        f"  {metrics['over_count']} of {metrics['vendor_count']} vendors above market\n"
        f"  Renewals in next {metrics['window_days']} days: {metrics['renewal_count']} "
        f"({metrics['renewal_dates']})\n\n"
        f"Vendors (keep order and count exactly):\n" + "\n".join(lines) + top_line
        + "\n\nWrite directly to the business owner. Practical, specific, no jargon. "
        "Actions must be terse and actionable; the highest-gap vendor's action should be the "
        "most urgent (e.g. 'Renegotiate now')."
    )


_SYSTEM_PROMPT = (
    "You are Rate Watch, EchoFrame's vendor-benchmarking engine. You tell a small-business "
    "owner which vendors are priced above the local market and what to do about each one.\n\n"
    "RULES:\n"
    "  • All dollar figures and rates are supplied by a verified engine. Copy them exactly; "
    "never invent, re-round, or recompute.\n"
    "  • Return exactly one action per supplied vendor, same order, with the matching index.\n"
    "  • Actions are 2-4 words, imperative, specific. At-market vendors get 'Hold'.\n"
    "  • The Benchmarking Note frames Over/Under as an annualized starting estimate, not a "
    "guaranteed saving. Never overpromise.\n"
    "  • Be concrete and useful. No filler, no hedging, no markdown."
)


def _generate_narrative(df, meta, metrics):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        system=_SYSTEM_PROMPT,
        tools=[RATE_WATCH_TOOL],
        tool_choice={"type": "tool", "name": "write_rate_watch_report"},
        messages=[{"role": "user", "content": _build_prompt(df, meta, metrics)}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "write_rate_watch_report":
            return block.input
    raise RuntimeError("[RateWatch] Claude returned no tool_use block.")


# ── Step 4: assemble the Jinja2 context ─────────────────────────────────────────

def _sources_line(industry: str) -> str:
    q = f"Q{(datetime.now().month - 1)//3 + 1} {datetime.now().year}"
    ind = industry.strip() or "service-category"
    return (f"Sources: IBISWorld {ind} averages · regional merchant-services benchmarks · "
            f"local commercial real-estate comps · EchoFrame vendor rate index ({q}).")


def _build_context(df, meta, metrics, prose, tier, is_sample) -> dict:
    tier = (tier or "core").lower()
    tier = tier if tier in TIER_LABELS else "core"

    by_index = {int(v.get("index", n)): v for n, v in enumerate(prose["vendors"])}
    top = metrics["top_index"]

    vendors = []
    for i in metrics["order"]:                      # render largest gap first
        r = df.loc[i]
        op = float(r["Overpayment"])
        v = by_index.get(i, {})
        vendors.append({
            "vendor": str(r["Vendor"]),
            "detail": str(r["Detail"]).strip(),
            "current_rate": str(r["Current Rate"]),
            "market_rate": str(r["Market Rate"]),
            "gap_label": (f"+{_money(op)}" if op > 0 else "At market"),
            "gap_class": ("over" if op > 0 else "at"),
            "renewal": _fmt_renewal(r["Renewal"]),
            "action": v.get("action", "Hold"),
            "action_go": (i == top and op > 0),
            "top": (i == top and op > 0),
        })

    kpis = [
        {"label": "Total Vendor Spend", "value": _money(metrics["total_spend"]), "unit": "/yr",
         "delta_class": "flat",
         "delta_text": f"Annualized across {metrics['vendor_count']} active vendors"},
        {"label": "Estimated Overpayment", "value": _money(metrics["total_over"]), "unit": "/yr",
         "delta_class": "down",
         "delta_text": f"▲ {metrics['over_pct']:.1f}% of vendor spend above market"},
        {"label": f"Renewals · Next {metrics['window_days']} Days",
         "value": str(metrics["renewal_count"]), "unit": "",
         "delta_class": "flat", "delta_text": metrics["renewal_dates"]},
    ]

    industry = meta.get("Industry", "")
    ctx = {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME,
        "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""),
        "tier": tier, "tier_label": TIER_LABELS[tier],
        "is_sample": is_sample,
        "vendor_count": metrics["vendor_count"],
        "kpis": kpis,
        "vendors": vendors,
        "total_overpayment_label": f"+{_money(metrics['total_over'])}/yr",
        "benchmarking_note": prose["benchmarking_note"],
        "sources": _sources_line(industry),
        "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]},
        "pro_note": None,
    }
    if tier == "pro":
        ctx["pro_note"] = (
            "<b>Pro re-benchmarking:</b> these rates are refreshed quarterly, so next quarter's "
            "report will re-test every vendor against the moving local market — including the "
            "ones at market today."
        )
    return ctx


# ── Step 5: render, persist, deliver ────────────────────────────────────────────

def _render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    return env.get_template("rate_watch.html.j2").render(**ctx)


def _save_report(meta, tier, html) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    slug = _report_slug(meta.get("Business Name", ""))
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"EchoFrame_RateWatch_{tier}_{slug}_{ts}.html"
    path.write_text(html, encoding="utf-8")
    print(f"[RateWatch] Report saved -> {path.name}")
    return str(path)


def _send_report_email(customer_email, owner_name, html_bytes, meta, tier):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", datetime.now().strftime("%B %Y")).strip()
    biz   = meta.get("Business Name", "your business").strip() or "your business"
    greet = (owner_name or "").strip() or "there"
    fname = f"EchoFrame_RateWatch_{month.replace(' ', '_')}.html"
    email_from = os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")
    body = (
        f"<p>Hi {greet},</p>"
        f"<p>Your {month} Rate Watch report for {biz} is attached and shown below — every "
        f"vendor benchmarked against the current local market, your upcoming renewals, and the "
        f"one renegotiation worth the most this cycle.</p>"
        f"<p>Reply with any questions.</p>"
        f"<p>— EchoFrame<br><span style=\"color:#6B7280;font-size:12px;\">Business intelligence, "
        f"not accounting software. Benchmark estimates are starting points, not guaranteed savings.</span></p>"
    )
    resend.Emails.send({
        "from": email_from, "to": [customer_email],
        "subject": f"Your {month} Rate Watch — {biz}".strip(),
        "html": body,
        "attachments": [{
            "filename": fname,
            "content": base64.b64encode(html_bytes).decode("ascii"),
            "content_type": "text/html",
        }],
    })
    print("[RateWatch] Report email dispatched.")  # no PII in logs


# ── Public entry point ──────────────────────────────────────────────────────────

def generate_rate_watch_report(
    customer_email: str,
    customer_name: str = "Client",
    tier: str = "",
    send_email: bool = True,
) -> str:
    df, meta = _load_vendors(customer_email)
    if df is None:
        return ""
    if not meta.get("Owner Name", "").strip():
        meta["Owner Name"] = customer_name.strip() or "Client"
    tier = (tier or meta.get("Tier", "core")).lower()
    window = TIER_WINDOWS.get(tier if tier in TIER_LABELS else "core", 60)

    metrics = _calculate_metrics(df, meta, window)
    prose   = _generate_narrative(df, meta, metrics)
    ctx     = _build_context(df, meta, metrics, prose, tier, is_sample=False)
    html    = _render_html(ctx)
    path    = _save_report(meta, ctx["tier"], html)

    if send_email:
        _send_report_email(customer_email, meta["Owner Name"],
                           Path(path).read_bytes(), meta, ctx["tier"])
    print(f"[RateWatch] Pipeline complete -> {customer_email} ({ctx['tier']})")
    return path


def render_from_csv(csv_path, tier: str, prose: dict, is_sample: bool = True) -> str:
    """Offline render path (no API call): caller supplies the prose dict."""
    df, meta = load_vendors_path(csv_path)
    if df is None:
        return ""
    window  = TIER_WINDOWS.get((tier or "core").lower(), 60)
    metrics = _calculate_metrics(df, meta, window)
    ctx = _build_context(df, meta, metrics, prose, tier, is_sample=is_sample)
    return _save_report(meta, ctx["tier"], _render_html(ctx))
