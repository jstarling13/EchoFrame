"""
EchoFrame — Rival Scan report engine
─────────────────────────────────────────────────────────────────────────────
Same separation of concerns as the other product engines:

  pandas   ─ ALL math: competitor count, price ranking / position label,
             change tally vs prior month, review totals.
  Claude   ─ ONLY prose via tool_use: the "What Moved This Week" bullets and
             "The One Thing To Do This Week" (title, body, steps, impact, risk).
  Jinja2   ─ ALL document structure (templates/rival_scan.html.j2).
  Resend   ─ email delivery with the HTML report.

Single tier ($129/mo) — no tier gating.

CSV format  (uploads/<safe_email>.csv)
─────────────────────────────────────────────────────────────────────────────
Rows whose first cell starts with `_` are metadata. A header row equal to
`Competitor,Key Price,Rating,Reviews,Promotion,Change,You` (case-insensitive on
the first three tokens) starts the competitor list. Mark your own business with
`yes` in the You column.

Example:
  _Business Name,Tony's Brick Oven Pizza
  _Owner Name,Tony
  _Industry,Pizza Restaurant
  _Location,Columbus GA
  _Month,June 2026
  _Radius,Within 4 mi of Broadway
  _Compare Label,Large 1-Topping Pizza
  _Price Unit,Lg 1-Topping
  _Changes This Month,7
  _Changes Prior,4
  _Prior Month,May
  Competitor,Key Price,Rating,Reviews,Promotion,Change,You
  Tony's Brick Oven,15.99,4.6,412,None active,,yes
  Marco's Pizza – Macon Rd,13.99,4.1,530,Online large 1-top $9.99 (PIZZA10),-2.00,
  Mellow Mushroom,18.50,4.3,1240,2 for $24 large cheese (ends 6/15),1.00,
  Fountain City Pizza Co.,16.50,4.7,286,Free garlic knots over $25,,
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

PRODUCT_NAME    = "Rival Scan"
PRODUCT_TAGLINE = "Local Competitive Monitoring"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
_PROMPT_DELIMITER_RE = re.compile(r'<<<[A-Z_]*>>>')
_HEADER_TOKENS = {"competitor", "key price", "rating"}
_VALID_TONES = {"threat", "watch", "opportunity", "neutral"}


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
        return float(str(s).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _is_truthy(s) -> bool:
    return str(s).strip().lower() in {"yes", "y", "true", "1", "x", "you"}


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


# ── Step 1: CSV ingestion ───────────────────────────────────────────────────────

def _load_rivals(customer_email: str):
    return load_rivals_path(UPLOADS_DIR / f"{_safe_email(customer_email)}.csv")


def load_rivals_path(path: Path):
    """Parse a competitor CSV into (rivals_df, meta_dict). Public for demo use."""
    path = Path(path)
    if not path.exists():
        print(f"[RivalScan] ERROR - no CSV found at: {path}")
        return None, {}

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))

    meta, crows, in_list = {}, [], False
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
        crows.append(cells)

    if not crows:
        print("[RivalScan] ERROR - no competitor rows found after header.")
        return None, meta

    cols = ["Competitor", "Key Price", "Rating", "Reviews", "Promotion", "Change", "You"]
    norm = [(r + [""] * len(cols))[:len(cols)] for r in crows]
    df = pd.DataFrame(norm, columns=cols)
    df["KeyPriceNum"] = df["Key Price"].map(_to_float)
    df["RatingNum"]   = df["Rating"].map(_to_float)
    df["ReviewsNum"]  = df["Reviews"].map(lambda x: int(_to_float(x)))
    df["ChangeNum"]   = df["Change"].map(lambda x: _to_float(x) if str(x).strip() else None)
    df["IsYou"]       = df["You"].map(_is_truthy)
    df = df.reset_index(drop=True)
    print(f"[RivalScan] Loaded {len(df)} rows ({int(df['IsYou'].sum())} marked 'you') from {path.name}")
    return df, meta


# ── Step 2: all math in pandas ──────────────────────────────────────────────────

def _calculate_metrics(df: pd.DataFrame, meta: dict) -> dict:
    n_total       = len(df)
    n_competitors = int((~df["IsYou"]).sum())

    you = df[df["IsYou"]]
    you_price = float(you["KeyPriceNum"].iloc[0]) if len(you) else None

    # Price position: rank your price ascending among all tracked (1 = lowest).
    position_label, position_sub = "—", f"of {n_total} tracked"
    if you_price is not None:
        rank = int((df["KeyPriceNum"] < you_price).sum()) + 1  # ties → share lower rank
        if rank == 1:
            position_label = "Lowest Price"
        elif rank == n_total:
            position_label = "Premium"
        else:
            position_label = "Mid-Market"
        position_sub = f"{_ordinal(rank)}-lowest of {n_total} tracked"

    # Changes this month vs prior — tracked monthly tally (metadata), with fallback.
    changes_now = meta.get("Changes This Month", "")
    changes_now = int(_to_float(changes_now)) if str(changes_now).strip() else \
        int(df["ChangeNum"].notna().sum())
    changes_prior_raw = meta.get("Changes Prior", "")
    changes_prior = int(_to_float(changes_prior_raw)) if str(changes_prior_raw).strip() else None
    prior_month = meta.get("Prior Month", "last month").strip() or "last month"

    new_reviews = df["ReviewsNum"].sum()  # available if needed by narrative

    print(f"[RivalScan] {n_competitors} competitors | your price "
          f"{('$%.2f' % you_price) if you_price is not None else 'n/a'} -> {position_label} "
          f"({position_sub}) | {changes_now} changes this month")

    return {
        "n_total": n_total, "n_competitors": n_competitors,
        "you_price": you_price,
        "position_label": position_label, "position_sub": position_sub,
        "changes_now": changes_now, "changes_prior": changes_prior,
        "prior_month": prior_month, "total_reviews": int(new_reviews),
        "radius": meta.get("Radius", "").strip(),
    }


# ── Step 3: Claude via tool_use — analysis prose only ───────────────────────────

RIVAL_SCAN_TOOL = {
    "name": "write_rival_scan_report",
    "description": (
        "Write the competitive-analysis prose for a Rival Scan report. All prices, "
        "ratings and counts are pre-calculated and supplied — never invent or alter a "
        "number. Return prose only: no markdown, no tables."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "what_moved": {
                "type": "array",
                "description": "3-4 bullets on what changed in the competitive set this week.",
                "items": {
                    "type": "object",
                    "properties": {
                        "tone": {"type": "string", "enum": ["threat", "watch", "opportunity", "neutral"],
                                 "description": "threat=hurts you, watch=monitor, opportunity=helps you, neutral=context."},
                        "text": {"type": "string", "description": "One bullet, starting with a bolded lead phrase in <b>...</b> followed by the detail. ~20-35 words."},
                    },
                    "required": ["tone", "text"],
                },
            },
            "one_thing_title": {"type": "string", "description": "Imperative headline for the single best move this week."},
            "one_thing_body": {"type": "string", "description": "2-3 sentences: the competitive logic and the recommended play. No markdown."},
            "one_thing_steps": {
                "type": "array", "items": {"type": "string"},
                "description": "Exactly 3 concrete, verb-first execution steps. Each one sentence.",
            },
            "one_thing_impact": {"type": "string", "description": "One clause quantifying the upside or defended revenue, framed as an estimate. Begins WITHOUT the words 'Estimated impact:' (the template adds that)."},
            "one_thing_risk": {"type": "string", "description": "One sentence naming the main risk and how to fence it. Begins WITHOUT the word 'Risk:' (the template adds that)."},
        },
        "required": ["what_moved", "one_thing_title", "one_thing_body",
                     "one_thing_steps", "one_thing_impact", "one_thing_risk"],
    },
}


def _build_prompt(df, meta, metrics):
    biz      = _sanitize(meta.get("Business Name", "the business"), 200)
    industry = _sanitize(meta.get("Industry", "small business"), 100)
    location = _sanitize(meta.get("Location", ""), 150)
    month    = _sanitize(meta.get("Month", ""), 30)
    label    = _sanitize(meta.get("Compare Label", "key product"), 80)

    lines = []
    for _, r in df.iterrows():
        tag = " (YOU)" if r["IsYou"] else ""
        chg = (f"{r['ChangeNum']:+.2f} vs last month" if r["ChangeNum"] is not None else "no change")
        promo = str(r["Promotion"]).strip() or "none"
        lines.append(
            f"  {r['Competitor']}{tag}: ${r['KeyPriceNum']:.2f} | "
            f"{r['RatingNum']}★ ({r['ReviewsNum']:,} reviews) | promo: {promo} | price {chg}"
        )

    prior = (f"{metrics['changes_prior']} in {metrics['prior_month']}"
             if metrics["changes_prior"] is not None else "no prior comparison")

    return (
        f"Business: {biz} ({industry}{', ' + location if location else ''}). Month: {month}.\n"
        f"Comparison metric: {label}.\n\n"
        f"Pre-calculated figures (use verbatim):\n"
        f"  Competitors tracked: {metrics['n_competitors']}{(' — ' + metrics['radius']) if metrics['radius'] else ''}\n"
        f"  Your price position: {metrics['position_label']} ({metrics['position_sub']})\n"
        f"  Changes this month: {metrics['changes_now']} (vs {prior})\n\n"
        f"Competitive set on {label}:\n" + "\n".join(lines)
        + "\n\nWrite directly to the owner. Be specific and tactical. The recommended move "
        "should protect margin and the core business, not start a price war. Use only the "
        "prices and figures above."
    )


_SYSTEM_PROMPT = (
    "You are Rival Scan, EchoFrame's local competitive-monitoring engine. You tell a "
    "small-business owner what changed in their competitive set and the single highest-leverage "
    "response — without telling them to start a price war.\n\n"
    "RULES:\n"
    "  • All prices, ratings, and counts are supplied by a verified engine. Copy them exactly; "
    "never invent, re-round, or recompute.\n"
    "  • 'what_moved' tones: threat (hurts you), watch (monitor), opportunity (helps you), "
    "neutral (context). Pick the honest tone per bullet.\n"
    "  • The One Thing protects margin and the core/dine-in or core business; prefer a fenced, "
    "targeted counter over matching a competitor's loss-leader.\n"
    "  • Be concrete and useful. No filler, no hedging, no markdown."
)


def _generate_narrative(df, meta, metrics):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        system=_SYSTEM_PROMPT,
        tools=[RIVAL_SCAN_TOOL],
        tool_choice={"type": "tool", "name": "write_rival_scan_report"},
        messages=[{"role": "user", "content": _build_prompt(df, meta, metrics)}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "write_rival_scan_report":
            return block.input
    raise RuntimeError("[RivalScan] Claude returned no tool_use block.")


# ── Step 4: assemble the Jinja2 context ─────────────────────────────────────────

def _build_context(df, meta, metrics, prose, is_sample) -> dict:
    competitors = []
    for _, r in df.iterrows():
        chg_num = r["ChangeNum"]
        if chg_num is None or pd.isna(chg_num) or chg_num == 0:
            change_html, chg_class = "—", "none"
        else:
            arrow = "▼" if chg_num < 0 else "▲"
            sign  = "−" if chg_num < 0 else "+"
            change_html, chg_class = f"{arrow} {sign}${abs(chg_num):.2f}", "alert"
        promo = str(r["Promotion"]).strip()
        promo_none = (promo == "" or promo.lower() in {"none", "none active", "n/a"})
        competitors.append({
            "name": str(r["Competitor"]),
            "you": bool(r["IsYou"]),
            "price": f"${r['KeyPriceNum']:.2f}",
            "rating": f"{r['RatingNum']:g}★ ({r['ReviewsNum']:,})",
            "promo": ("None active" if promo_none else promo),
            "promo_none": promo_none,
            "change": change_html,
            "chg_class": chg_class,
        })

    # Changes-this-month delta styling (more activity = an alert, shown red/up).
    if metrics["changes_prior"] is not None:
        delta = metrics["changes_now"] - metrics["changes_prior"]
        if delta > 0:
            chg_sub, chg_sub_cls = (f"▲ up from {metrics['changes_prior']} in {metrics['prior_month']}", "up")
        elif delta < 0:
            chg_sub, chg_sub_cls = (f"▼ down from {metrics['changes_prior']} in {metrics['prior_month']}", "down")
        else:
            chg_sub, chg_sub_cls = (f"Same as {metrics['prior_month']}", "flat")
    else:
        chg_sub, chg_sub_cls = ("Tracked this month", "flat")

    kpis = [
        {"label": "Competitors Tracked", "value": str(metrics["n_competitors"]),
         "is_text": False, "sub": (metrics["radius"] or "In your local market"), "sub_class": "flat"},
        {"label": "Changes This Month", "value": str(metrics["changes_now"]),
         "is_text": False, "sub": chg_sub, "sub_class": chg_sub_cls},
        {"label": "Your Price Position", "value": metrics["position_label"],
         "is_text": True, "sub": metrics["position_sub"], "sub_class": "flat"},
    ]

    # Validate Claude tones; fall back to neutral.
    moved = []
    for m in prose["what_moved"]:
        tone = m.get("tone", "neutral")
        moved.append({"tone": tone if tone in _VALID_TONES else "neutral",
                      "text": m.get("text", "")})

    return {
        "biz_name": meta.get("Business Name", "Your Business"),
        "product_name": PRODUCT_NAME,
        "product_tagline": PRODUCT_TAGLINE,
        "month": meta.get("Month", datetime.now().strftime("%B %Y")),
        "location": meta.get("Location", ""),
        "is_sample": is_sample,
        "compare_label": meta.get("Compare Label", "Key Product"),
        "price_unit": meta.get("Price Unit", meta.get("Compare Label", "Key Price")),
        "kpis": kpis,
        "competitors": competitors,
        "what_moved": moved,
        "one_thing": {
            "title": prose["one_thing_title"],
            "body": prose["one_thing_body"],
            "steps": prose["one_thing_steps"],
            "impact": prose["one_thing_impact"],
            "risk": prose["one_thing_risk"],
        },
    }


# ── Step 5: render, persist, deliver ────────────────────────────────────────────

def _render_html(ctx: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "j2"]),
    )
    return env.get_template("rival_scan.html.j2").render(**ctx)


def _save_report(meta, html) -> str:
    REPORTS_DIR.mkdir(exist_ok=True)
    slug = _report_slug(meta.get("Business Name", ""))
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"EchoFrame_RivalScan_{slug}_{ts}.html"
    path.write_text(html, encoding="utf-8")
    print(f"[RivalScan] Report saved -> {path.name}")
    return str(path)


def _send_report_email(customer_email, owner_name, html_bytes, meta):
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    month = meta.get("Month", datetime.now().strftime("%B %Y")).strip()
    biz   = meta.get("Business Name", "your business").strip() or "your business"
    greet = (owner_name or "").strip() or "there"
    fname = f"EchoFrame_RivalScan_{month.replace(' ', '_')}.html"
    email_from = os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>")
    body = (
        f"<p>Hi {greet},</p>"
        f"<p>Your {month} Rival Scan for {biz} is attached and shown below — your local "
        f"competitors' pricing, reviews, and promotions, what moved this week, and the one "
        f"move worth making.</p>"
        f"<p>Reply with any questions.</p>"
        f"<p>— EchoFrame<br><span style=\"color:#6B7280;font-size:12px;\">Business intelligence, "
        f"not accounting software. Competitive data is monitored from public sources.</span></p>"
    )
    resend.Emails.send({
        "from": email_from, "to": [customer_email],
        "subject": f"Your {month} Rival Scan — {biz}".strip(),
        "html": body,
        "attachments": [{
            "filename": fname,
            "content": base64.b64encode(html_bytes).decode("ascii"),
            "content_type": "text/html",
        }],
    })
    print("[RivalScan] Report email dispatched.")  # no PII in logs


# ── Public entry point ──────────────────────────────────────────────────────────

def generate_rival_scan_report(
    customer_email: str,
    customer_name: str = "Client",
    tier: str = "",          # single-tier product; accepted for router uniformity
    send_email: bool = True,
) -> str:
    df, meta = _load_rivals(customer_email)
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
    print(f"[RivalScan] Pipeline complete -> {customer_email}")
    return path


def render_from_csv(csv_path, prose: dict, is_sample: bool = True) -> str:
    """Offline render path (no API call): caller supplies the prose dict."""
    df, meta = load_rivals_path(csv_path)
    if df is None:
        return ""
    metrics = _calculate_metrics(df, meta)
    ctx = _build_context(df, meta, metrics, prose, is_sample=is_sample)
    return _save_report(meta, _render_html(ctx))
