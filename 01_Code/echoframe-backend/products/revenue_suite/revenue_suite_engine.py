"""
EchoFrame — Revenue Suite report engine
─────────────────────────────────────────────────────────────────────────────
Combines the three revenue products into one report:
  Call Catch (missed-call recovery) + Quote Revive (quote follow-up) +
  Clear Ledger (invoice collections, Growth tier).

It reuses each product engine's parser + math, then:
  pandas/engines ─ all per-product numbers (revenue saved, reactivated, collected).
  Claude         ─ ONLY the intro line, the suite note, and the combined One Thing.
  Jinja2         ─ templates/revenue_suite.html.j2 ; Resend ─ delivery.

Intake: three CSVs (one per product). In production, looked up per email as
  <safe_email>_callcatch.csv / _quoterevive.csv / _clearledger.csv.
Single plan ($199/mo).
"""

import os, re, base64
import data_quality
import html_safe
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from products.call_catch import call_catch_engine as cc
from products.quote_revive import quote_revive_engine as qr
from products.clear_ledger import clear_ledger_engine as cl

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = Path(os.environ.get("ECHOFRAME_UPLOADS_DIR") or BASE_DIR.parent.parent / "uploads"); REPORTS_DIR = Path(os.environ.get("ECHOFRAME_REPORTS_DIR") or BASE_DIR.parent.parent / "reports"); TEMPLATES_DIR = BASE_DIR
PRODUCT_NAME = "Revenue Suite"
PRODUCT_TAGLINE = "Call Catch + Quote Revive + Clear Ledger"

_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')

def _safe_email(e):
    e = e.strip().lower(); l, _, d = e.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', l)}_at_{_SAFE_CHAR_RE.sub('_', d)}"
def _slug(b): s = re.sub(r"[^a-z0-9]+", "_", (b or "").lower()).strip("_"); return s or "report"
def _money(n): return f"${n:,.0f}"


def _load_all(cc_path, qr_path, cl_path):
    cc_df, cc_meta = cc.load_path(cc_path)
    qr_df, qr_meta = qr.load_path(qr_path)
    cl_df, cl_meta = cl.load_path(cl_path)
    if cc_df is None or qr_df is None or cl_df is None:
        return None
    return {
        "cc": {"df": cc_df, "meta": cc_meta, "m": cc._metrics(cc_df, cc_meta)},
        "qr": {"df": qr_df, "meta": qr_meta, "m": qr._metrics(qr_df, qr_meta)},
        "cl": {"df": cl_df, "meta": cl_meta, "m": cl._metrics(cl_df, cl_meta)},
    }


def _combine(parts, meta):
    ccm, qrm, clm = parts["cc"]["m"], parts["qr"]["m"], parts["cl"]["m"]
    total = ccm["rev_saved"] + qrm["rev_react"] + clm["collected"]
    biz = meta.get("Business Name") or parts["cc"]["meta"].get("Business Name", "Your Business")
    month = meta.get("Month") or parts["cc"]["meta"].get("Month", datetime.now().strftime("%B %Y"))
    print(f"[RevenueSuite] total recovered ${total:,.0f} "
          f"(CC ${ccm['rev_saved']:,.0f} + QR ${qrm['rev_react']:,.0f} + CL ${clm['collected']:,.0f})")
    return {"total": total, "biz": biz, "month": month,
            "location": meta.get("Location") or parts["cc"]["meta"].get("Location", ""),
            "cc": ccm, "qr": qrm, "cl": clm}


SUITE_TOOL = {
    "name": "write_revenue_suite_report",
    "description": "Write the intro line, suite note, and combined One Thing for a Revenue Suite report "
                   "that aggregates three tools. All figures are supplied — never invent one.",
    "input_schema": {"type": "object", "properties": {
        "intro_note": {"type": "string", "description": "1-2 short sentences for the hero card summarizing total recovered across the three tools this month. May use <b>...</b>."},
        "suite_note": {"type": "string", "description": "One paragraph on how the three tools plug the three revenue leak points (missed call, cold quote, unpaid invoice) on one bill. May use <b>...</b>."},
        "one_thing_title": {"type": "string", "description": "Headline naming the single highest-leverage action across all three tools this month."},
        "one_thing_body": {"type": "string", "description": "3-4 sentences identifying the biggest single lever among the three products and the action. Wrap dollar figures in <span class=\"dollar\">...</span>. Use only supplied numbers."},
    }, "required": ["intro_note", "suite_note", "one_thing_title", "one_thing_body"]},
}

_SYSTEM = ("You are EchoFrame's Revenue Suite, summarizing three revenue-recovery tools on one report. "
           "All dollar figures are supplied by verified engines — copy them exactly, never invent. No markdown.")

def _prompt(c):
    return (f"Business: {c['biz']}. Month: {c['month']}.\n\n"
            f"Pre-calculated totals (use verbatim):\n"
            f"  Total recovered: {_money(c['total'])}\n"
            f"  Call Catch: {_money(c['cc']['rev_saved'])} saved · {c['cc']['recovered']} leads recovered of {c['cc']['missed']} missed ({c['cc']['rec_pct']}%)\n"
            f"  Quote Revive: {_money(c['qr']['rev_react'])} reactivated · {c['qr']['jobs']} jobs closed · {c['qr']['revived']}/{c['qr']['cold_count']} revived\n"
            f"  Clear Ledger: {_money(c['cl']['collected'])} collected · {c['cl']['open_count']} invoices, {_money(c['cl']['total_overdue'])} still overdue · avg days-to-pay {c['cl']['prior_days']}→{c['cl']['avg_days']}\n\n"
            f"Write to the owner. The One Thing is the single biggest lever across all three tools.")

def _narrative(c):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    r = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=1600, system=_SYSTEM,
        tools=[SUITE_TOOL], tool_choice={"type": "tool", "name": "write_revenue_suite_report"},
        messages=[{"role": "user", "content": _prompt(c)}])
    for b in r.content:
        if b.type == "tool_use": return b.input
    raise RuntimeError("[RevenueSuite] no tool_use")


def _context(c, prose, is_sample):
    ccm, qrm, clm = c["cc"], c["qr"], c["cl"]
    kpis = [
        {"label": "Call Catch", "value": _money(ccm["rev_saved"]),
         "delta_text": f"{ccm['recovered']} leads recovered"},
        {"label": "Quote Revive", "value": _money(qrm["rev_react"]),
         "delta_text": f"{qrm['jobs']} jobs closed"},
        {"label": "Clear Ledger", "value": _money(clm["collected"]),
         "delta_text": f"{clm.get('cleared') or 0} invoices cleared"},
    ]
    modules = [
        {"name": "Call Catch", "price": "$79/mo", "stat": _money(ccm["rev_saved"]), "stat_label": "saved",
         "lines": [f"{ccm['missed']} missed calls → {ccm['recovered']} recovered ({ccm['rec_pct']}%)",
                   f"Every call texted back in ~{ccm['avg_send']}"],
         "top_label": "Biggest catch:", "top_value": "after-hours emergency calls booked overnight"},
        {"name": "Quote Revive", "price": "$99/mo", "stat": _money(qrm["rev_react"]), "stat_label": "reactivated",
         "lines": [f"{qrm['cold_count']} cold quotes worked → {qrm['revived']} revived, {qrm['jobs']} closed",
                   f"{_money(qrm['open_value'])} open pipeline at month start"],
         "top_label": "Biggest live quote:", "top_value": "engaged but unclosed — worth a personal call"},
        {"name": "Clear Ledger", "price": "$99/mo", "stat": _money(clm["collected"]), "stat_label": "collected",
         "lines": [f"{_money(clm['total_overdue'])} still overdue across {clm['open_count']} invoices",
                   f"Avg days-to-pay {clm['prior_days']} → {clm['avg_days']}"],
         "top_label": "Oldest balance:", "top_value": "flagged for owner handoff"},
    ]
    return {"biz_name": c["biz"], "product_name": PRODUCT_NAME, "product_tagline": PRODUCT_TAGLINE,
            "month": c["month"], "location": c["location"], "is_sample": is_sample,
            "total_recovered": _money(c["total"]), "kpis": kpis, "modules": modules,
            "intro_note": prose["intro_note"], "suite_note": prose["suite_note"],
            "one_thing": {"title": prose["one_thing_title"], "body": prose["one_thing_body"]}}


def _render(ctx):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=select_autoescape(["html", "j2"]))
    env.filters["clean"] = html_safe.clean
    return env.get_template("revenue_suite.html.j2").render(**ctx)
def _save(biz, html):
    REPORTS_DIR.mkdir(exist_ok=True)
    p = REPORTS_DIR / f"EchoFrame_RevenueSuite_{_slug(biz)}_{datetime.now():%Y%m%d_%H%M%S}.html"
    p.write_text(html, encoding="utf-8"); print(f"[RevenueSuite] Report saved -> {p.name}"); return str(p)
def _email(email, owner, html_bytes, biz, month, dq_warnings=None):
    import resend
    from pdf_render import report_attachment
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    params = {"from": os.environ.get("EMAIL_FROM", "EchoFrame <reports@echoframe.net>"),
        "to": [email], "subject": f"Your {month} Revenue Suite — {biz}".strip(),
        "html": f"<p>Hi {(owner or 'there').strip()},</p><p>Your {month} Revenue Suite report for {biz} is "
                f"attached — Call Catch, Quote Revive, and Clear Ledger on one page, with everything you "
                f"recovered this month and the one move worth making next.</p><p>— EchoFrame</p>",
        "attachments": [report_attachment(html_bytes, f"EchoFrame_RevenueSuite_{month.replace(' ','_')}.html")]}
    if dq_warnings: params["_dq_warnings"] = list(dq_warnings)
    resend.Emails.send(params)
    print("[RevenueSuite] Report email dispatched.")


def generate_revenue_suite_report(customer_email, customer_name="Client", tier="", send_email=True):
    stem = _safe_email(customer_email)
    parts = _load_all(UPLOADS_DIR / f"{stem}_callcatch.csv",
                      UPLOADS_DIR / f"{stem}_quoterevive.csv",
                      UPLOADS_DIR / f"{stem}_clearledger.csv")
    if parts is None:
        print("[RevenueSuite] ERROR - missing one or more of the three product CSVs."); return ""

    # Data-quality gate (B-1): each of the three feeds was parsed by its own engine
    # (which stamped dq signals onto df.attrs). Surface any per-feed trouble as
    # warnings on the review email so a messy feed can't silently skew the combined
    # total. We don't hard-fail the whole suite here — the human reviewer decides.
    dq_warnings = []
    for key, label, ncols in (("cc", "Call Catch", []), ("qr", "Quote Revive", []),
                              ("cl", "Clear Ledger", ["Amount"])):
        sub = data_quality.assess(parts[key]["df"], numeric_cols=ncols,
                                  label=f"Revenue Suite · {label}")
        dq_warnings.extend(f"{label}: {line}" for line in sub.banner_lines())

    c = _combine(parts, {})
    owner = customer_name.strip() or "Client"
    prose = _narrative(c)
    html = _render(_context(c, prose, is_sample=False))
    path = _save(c["biz"], html)
    if send_email: _email(customer_email, owner, Path(path).read_bytes(), c["biz"], c["month"],
                          dq_warnings=dq_warnings)
    print(f"[RevenueSuite] Pipeline complete -> {customer_email}")
    return path


def render_from_csvs(cc_path, qr_path, cl_path, prose, meta=None, is_sample=True):
    """Offline render path (no API call): caller supplies the combined prose dict."""
    parts = _load_all(cc_path, qr_path, cl_path)
    if parts is None: return ""
    c = _combine(parts, meta or {})
    return _save(c["biz"], _render(_context(c, prose, is_sample)))
