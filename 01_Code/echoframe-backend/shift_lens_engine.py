"""
EchoFrame — Shift Lens report engine
─────────────────────────────────────────────────────────────────────────────
Same separation of concerns as the other product engines:

  pandas   ─ ALL math: per-shift labor %, margin, week totals/blended rate,
             most/least profitable shift, and the deterministic flag/pill bands.
  Claude   ─ ONLY prose via tool_use: the Pattern Note paragraph and The One
             Thing (title + body).
  Jinja2   ─ ALL document structure (templates/shift_lens.html.j2).
  Resend   ─ email delivery with the HTML report.

Single tier ($149/mo) — no tier gating.

CSV format  (uploads/<safe_email>.csv)
─────────────────────────────────────────────────────────────────────────────
Rows whose first cell starts with `_` are metadata. A header row containing both
`Revenue` and `Labor Cost` (case-insensitive) starts the shift list.

Example:
  _Business Name,Foundry Coffee Co. LLC
  _Owner Name,Mara
  _Industry,Coffee Shop
  _Location,Columbus GA
  _Month,June 2026
  _Target Low,28
  _Target High,32
  _Burden,18
  _Period Label,one representative week
  Day / Shift,Detail,Revenue,Labor Cost
  Weekday Morning,Mon–Fri · 6–11 AM,4620,1010
  Weekday Midday,Mon–Fri · 11 AM–2 PM,2180,700
  ...

`Revenue` and `Labor Cost` are plain numbers for the period.
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

PRODUCT_NAME    = "Shift Lens"
PRODUCT_TAGLINE = "Labor cost vs. revenue by shift"

# Defaults if metadata omits them (limited-service coffee benchmark band).
DEFAULT_TARGET_LOW  = 28.0
DEFAULT_TARGET_HIGH = 32.0
DEFAULT_BURDEN      = 18.0

# Deterministic labor-% pill bands (reproduce the locked sample).
_PILL_AT_MAX   = 33.0   # <=33% → green "at"
_PILL_OVER_MIN = 50.0   # >=50% → red "over"; between → amber "warn"
# Deterministic flag bands (margin first, then labor %).
_FLAG_STRONG_MAX  = 28.0
_FLAG_HEALTHY_MAX = 42.0

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_PROMPT_DELIMITER_RE = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"revenue", "labor cost"}


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


def _signed_money(n: float) -> str:
    return (f"+${n:,.0f}" if n >= 0 else f"−${abs(n):,.0f}")


def _time_part(detail: str) -> str:
    """'Mon–Fri · 6–11 AM' -> '6–11 AM'; falls back to the whole detail."""
    parts = [p.strip() for p in str(detail).split("·")]
    return parts[-1] if parts and parts[-1] else str(detail).strip()


# ── Step 1: CSV ingestion ───────────────────────────────────────────────────────

def _load_shifts(customer_email: str):
    return load_shifts_path(UPLOADS_DIR / f"{_safe_email(customer_email)}.csv")


def load_shifts_path(path: Path):
    """Parse a shift CSV into (shifts_df, meta_dict). Public for demo use."""
    path = Path(path)
    if not path.exists():
        print(f"[ShiftLens] ERROR - no CSV found at: {path}")
        return None, {}

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))

    meta, srows, in_list = {}, [], False
    for row in rows:
        if not row:
            continue
        first = str(row[0]).strip()
        if first.startswith("_"):
            meta[first.lstrip("_").strip()] = str(row[1]).strip() if len(row) > 1 else ""
            continue
        cells = [str(c).strip() for c in row]
        if not in_list:
            if _HEADER_TOKENS.issubset({c.lower() for c in cells}):
                in_list = True
            continue
        if not first:
            continue
        srows.append(cells)

    if not srows:
        print("[ShiftLens] ERROR - no shift rows found after header.")
        return None, meta

    cols = ["Shift", "Detail", "Revenue", "Labor Cost"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in srows]
    df = pd.DataFrame(norm, columns=cols)
    df["RevenueNum"] = df["Revenue"].map(_to_float)
    df["LaborNum"]   = df["Labor Cost"].map(_to_float)
    df["LaborPct"]   = df.apply(
        lambda r: (r["LaborNum"] / r["RevenueNum"] * 100) if r["RevenueNum"] > 0 else 999.0, axis=1)
    df["MarginNum"]  = df["RevenueNum"] - df["LaborNum"]
    df = df.reset_index(drop=True)
    print(f"[ShiftLens] Loaded {len(df)} shifts from {path.name}")
    return df, meta


# ── Step 2: all math + deterministic classification in pandas ───────────────────

def _pill_class(labor_pct: float) -> str:
    if labor_pct <= _PILL_AT_MAX:
        return "at"
    if labor_pct >= _PILL_OVER_MIN:
        return "over"
    return "warn"


def _flag(labor_pct: float, margin: float) -> tuple:
    """Return (flag_text, flag_style) where style is '', 'warn', or 'over'."""
    if margin < 0:
        return ("Losing $", "over")
    if labor_pct < _FLAG_STRONG_MAX:
        return ("Strong", "")
    if labor_pct < _FLAG_HEALTHY_MAX:
        return ("Healthy", "")
    return ("Weak", "warn")


def _calculate_metrics(df: pd.DataFrame, meta: dict) -> dict:
    total_rev   = float(df["RevenueNum"].sum())
    total_labor = float(df["LaborNum"].sum())
    total_margin = total_rev - total_labor
    blended_pct = (total_labor / total_rev * 100) if total_rev > 0 else 0.0

    best_i  = int(df["MarginNum"].idxmax())
    worst_i = int(df["MarginNum"].idxmin())

    low  = _to_float(meta.get("Target Low", "")) or DEFAULT_TARGET_LOW
    high = _to_float(meta.get("Target High", "")) or DEFAULT_TARGET_HIGH

    print(f"[ShiftLens] {len(df)} shifts | rev ${total_rev:,.0f} labor ${total_labor:,.0f} "
          f"({blended_pct:.1f}% blended) margin {_signed_money(total_margin)} | "
          f"best={df.loc[best_i,'Shift']} worst={df.loc[worst_i,'Shift']}")

    return {
        "total_rev": total_rev, "total_labor": total_labor,
        "total_margin": total_margin, "blended_pct": blended_pct,
        "best_i": best_i, "worst_i": worst_i,
        "target_low": low, "target_high": high,
        "shift_count": len(df),
    }


# ── Step 3: Claude via tool_use — analysis prose only ───────────────────────────

SHIFT_LENS_TOOL = {
    "name": "write_shift_lens_report",
    "description": (
        "Write the analysis prose for a Shift Lens report. All dollar figures, labor "
        "percentages and margins are pre-calculated and supplied — never invent or alter a "
        "number. Return prose only: no markdown, no tables."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern_note": {
                "type": "string",
                "description": "One paragraph (~80-110 words) explaining the daypart/scheduling pattern behind the numbers: why the blended rate hides the problem, which shifts carry the business, where labor outruns demand, and that the issue is hours-vs-demand, not wage rates. May wrap key phrases in <b>...</b>.",
            },
            "one_thing_title": {"type": "string", "description": "Imperative headline for the single highest-leverage schedule change."},
            "one_thing_body": {"type": "string", "description": "3-4 sentences: name the money-losing/weakest shift, the specific cut or restructure, the weekly and monthly labor saved, the revenue given up, and the estimated net savings. Wrap dollar figures in <span class=\"dollar\">...</span>. Use only supplied numbers; protect the profitable shifts."},
        },
        "required": ["pattern_note", "one_thing_title", "one_thing_body"],
    },
}


def _build_prompt(df, meta, metrics):
    biz      = _sanitize(meta.get("Business Name", "the business"), 200)
    industry = _sanitize(meta.get("Industry", "small business"), 100)
    location = _sanitize(meta.get("Location", ""), 150)
    month    = _sanitize(meta.get("Month", ""), 30)

    lines = []
    for i, r in df.iterrows():
        flag, _ = _flag(r["LaborPct"], r["MarginNum"])
        lines.append(
            f"  {r['Shift']} ({r['Detail']}): rev ${r['RevenueNum']:,.0f} | "
            f"labor ${r['LaborNum']:,.0f} | {r['LaborPct']:.1f}% labor | "
            f"margin {_signed_money(r['MarginNum'])} | {flag}"
        )
    best, worst = df.loc[metrics["best_i"]], df.loc[metrics["worst_i"]]

    return (
        f"Business: {biz} ({industry}{', ' + location if location else ''}). Month: {month}.\n\n"
        f"Pre-calculated figures (use verbatim, never recompute):\n"
        f"  Week totals: revenue ${metrics['total_rev']:,.0f} | labor ${metrics['total_labor']:,.0f} "
        f"| blended {metrics['blended_pct']:.1f}% labor | margin {_signed_money(metrics['total_margin'])}\n"
        f"  Target labor band: {metrics['target_low']:.0f}–{metrics['target_high']:.0f}%\n"
        f"  Most profitable: {best['Shift']} ({best['LaborPct']:.1f}% labor, "
        f"{_signed_money(best['MarginNum'])})\n"
        f"  Least profitable: {worst['Shift']} ({worst['LaborPct']:.1f}% labor, "
        f"{_signed_money(worst['MarginNum'])})\n\n"
        f"Shifts:\n" + "\n".join(lines)
        + "\n\nWrite directly to the owner. The recommendation should cut or restructure the "
        "weakest/money-losing shifts and protect the profitable ones — not cut wages. Use only "
        "the figures above."
    )


_SYSTEM_PROMPT = (
    "You are Shift Lens, EchoFrame's shift-profitability engine. You show a small-business owner "
    "which shifts earn their keep and which bleed money, and the single best schedule change.\n\n"
    "RULES:\n"
    "  • All dollar figures, labor percentages, and margins are supplied by a verified engine. "
    "Copy them exactly; never invent, re-round, or recompute.\n"
    "  • The problem is almost always hours scheduled against demand, not wage rates — say so.\n"
    "  • The One Thing cuts/restructures the weakest shifts and explicitly protects the profitable "
    "ones. Quantify weekly and monthly savings and the revenue given up.\n"
    "  • Be concrete and useful. No filler, no hedging, no markdown."
)


def _generate_narrative(df, meta, metrics):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=_SYSTEM_PROMPT,
        tools=[SHIFT_LENS_TOOL],
        tool_choice={"type": "tool", "name": "write_shift_lens_report"},
        messages=[{"role": "user", "content": _build_prompt(df, meta, metrics)}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "write_shift_lens_report":
            return block.input
    raise RuntimeError("[ShiftLens] Claude returned no tool_use block.")


# ── Step 4: assemble the Jinja2 context ─────────────────────────────────────────

def _method_line(meta, metrics) -> str:
    burden   = _to_float(meta.get("Burden", "")) or DEFAULT_BURDEN
    industry = meta.get("Industry", "limited-service").strip() or "limited-service"
    q = f"Q{(datetime.now().month - 1)//3 + 1} {datetime.now().year}"
    return (f"Method: each shift's scheduled labor (wages + ~{burden:.0f}% payroll burden) measured "
            f"against POS revenue for the same hours. Targets from NRA / IBISWorld {industry} "
            f"benchmarks ({metrics['target_low']:.0f}–{metrics['target_high']:.0f}% labor). "
            f"EchoFrame shift index, {q}.")


def _build_context(df, meta, metrics, prose, is_sample) -> dict:
    worst_i = metrics["worst_i"]
    shifts = []
    for i, r in df.iterrows():
        flag_txt, flag_style = _flag(r["LaborPct"], r["MarginNum"])
        flag_html = (f'<span class="pill {flag_style}">{flag_txt}</span>' if flag_style else flag_txt)
        margin = r["MarginNum"]
        margin_html = (f'<span class="neg">{_money(margin)}</span>' if margin < 0 else _signed_money(margin))
        shifts.append({
            "shift": str(r["Shift"]),
            "detail": str(r["Detail"]).strip(),
            "revenue": _money(r["RevenueNum"]),
            "labor": _money(r["LaborNum"]),
            "labor_pct": f"{r['LaborPct']:.1f}%",
            "pill_class": _pill_class(r["LaborPct"]),
            "margin": margin_html,
            "flag": flag_html,
            "top": (i == worst_i and margin < 0),
        })

    best, worst = df.loc[metrics["best_i"]], df.loc[metrics["worst_i"]]

    # KPI 1 — total labor % vs target band.
    above = metrics["blended_pct"] > metrics["target_high"]
    labor_delta = (f"▲ Above the {metrics['target_low']:.0f}–{metrics['target_high']:.0f}% "
                   f"{meta.get('Industry','').strip().lower() or 'industry'} target" if above
                   else f"Within the {metrics['target_low']:.0f}–{metrics['target_high']:.0f}% target band")

    # KPI 2/3 — most & least profitable shift (two-line value).
    best_val  = f"{best['Shift']}<br>{_time_part(best['Detail'])}"
    worst_val = f"{worst['Shift']}<br>{_time_part(worst['Detail'])}"
    best_delta  = f"{best['LaborPct']:.1f}% labor · {_signed_money(best['MarginNum'])} margin"
    worst_delta = (f"{worst['LaborPct']:.0f}% labor · "
                   + ("loses money" if worst['MarginNum'] < 0 else f"{_signed_money(worst['MarginNum'])} margin"))

    kpis = [
        {"label": "Total Labor %", "value": f"{metrics['blended_pct']:.1f}%", "value_sm": False,
         "delta_class": "down" if above else "up", "delta_text": labor_delta},
        {"label": "Most Profitable Shift", "value": best_val, "value_sm": True,
         "delta_class": "up", "delta_text": best_delta},
        {"label": "Least Profitable Shift", "value": worst_val, "value_sm": True,
         "delta_class": "down", "delta_text": worst_delta},
    ]

    blended_pill = "warn" if metrics["blended_pct"] > metrics["target_high"] else "at"
    totals = {
        "label": "Week total · blended",
        "revenue": _money(metrics["total_rev"]),
        "labor": _money(metrics["total_labor"]),
        "labor_pct": f"{metrics['blended_pct']:.1f}%",
        "pill_class": blended_pill,
        "margin": _signed_money(metrics["total_margin"]),
    }

    return {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME,
        "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""),
        "is_sample": is_sample,
        "period_label": meta.get("Period Label", "one representative week"),
        "shift_count": metrics["shift_count"],
        "kpis": kpis,
        "shifts": shifts,
        "totals": totals,
        "pattern_note": prose["pattern_note"],
        "method_line": _method_line(meta, metrics),
        "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]},
    }


# ── Step 5: render, persist, deliver ────────────────────────────────────────────

def _render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    return env.get_template("shift_lens.html.j2").render(**ctx)


def _save_report(meta, html) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    slug = _report_slug(meta.get("Business Name", ""))
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"EchoFrame_ShiftLens_{slug}_{ts}.html"
    path.write_text(html, encoding="utf-8")
    print(f"[ShiftLens] Report saved -> {path.name}")
    return str(path)


def _send_report_email(customer_email, owner_name, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", datetime.now().strftime("%B %Y")).strip()
    biz   = meta.get("Business Name", "your business").strip() or "your business"
    greet = (owner_name or "").strip() or "there"
    fname = f"EchoFrame_ShiftLens_{month.replace(' ', '_')}.html"
    email_from = os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.co>")
    body = (
        f"<p>Hi {greet},</p>"
        f"<p>Your {month} Shift Lens report for {biz} is attached and shown below — every shift's "
        f"labor cost against the revenue it earns, which shifts pay off, and the one schedule "
        f"change worth making before the week starts.</p>"
        f"<p>Reply with any questions.</p>"
        f"<p>— EchoFrame<br><span style=\"color:#6B7280;font-size:12px;\">Business intelligence, "
        f"not accounting software. Estimates are starting points, not guaranteed savings.</span></p>"
    )
    resend.Emails.send({
        "from": email_from, "to": [customer_email],
        "subject": f"Your {month} Shift Lens — {biz}".strip(),
        "html": body,
        "attachments": [{
            "filename": fname,
            "content": base64.b64encode(html_bytes).decode("ascii"),
            "content_type": "text/html",
        }],
    })
    print("[ShiftLens] Report email dispatched.")  # no PII in logs


# ── Public entry point ──────────────────────────────────────────────────────────

def generate_shift_lens_report(
    customer_email: str,
    customer_name: str = "Client",
    tier: str = "",          # single-tier product; accepted for router uniformity
    send_email: bool = True,
) -> str:
    df, meta = _load_shifts(customer_email)
    if df is None:
        return ""
    if not meta.get("Owner Name", "").strip():
        meta["Owner Name"] = customer_name.strip() or "Client"

    metrics = _calculate_metrics(df, meta)
    prose   = _generate_narrative(df, meta, metrics)
    ctx     = _build_context(df, meta, metrics, prose, is_sample=False)
    html    = _render_html(ctx)
    path    = _save_report(meta, html)

    if send_email:
        _send_report_email(customer_email, meta["Owner Name"], Path(path).read_bytes(), meta)
    print(f"[ShiftLens] Pipeline complete -> {customer_email}")
    return path


def render_from_csv(csv_path, prose: dict, is_sample: bool = True) -> str:
    """Offline render path (no API call): caller supplies the prose dict."""
    df, meta = load_shifts_path(csv_path)
    if df is None:
        return ""
    metrics = _calculate_metrics(df, meta)
    ctx = _build_context(df, meta, metrics, prose, is_sample=is_sample)
    return _save_report(meta, _render_html(ctx))
