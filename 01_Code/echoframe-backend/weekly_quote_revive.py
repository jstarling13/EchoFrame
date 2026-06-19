"""
EchoFrame — Quote Revive WEEKLY digest
─────────────────────────────────────────────────────────────────────────────
Quote follow-up is time-sensitive, but a monthly report is too slow to drive it.
This turns the customer's last-uploaded open-quote list into a short *weekly*
"chase list": the few quotes most worth following up THIS week, the exact message
to send each one, and the single biggest one to call personally.

It needs no new work from the customer — they upload their open quotes ~monthly
with their billing cycle, and this paces the follow-ups out week by week. Each
week a quote's effective "days cold" advances, so its suggested touch escalates:
gentle check-in → value nudge → the decision ask → reactivation.

Delivery: a weekly cron (cron-job.org → /api/cron/weekly-quote-revive) calls
run_weekly(), which iterates everyone with a stored quote list and emails each
their digest via Resend. Claude writes the messages when ANTHROPIC_API_KEY is set;
otherwise a clean template fallback keeps it working (and keeps tests offline).
"""

from __future__ import annotations

import os
import csv
import time
import html
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import store

WEEK = 7 * 24 * 3600
MAX_ITEMS = 3                      # quotes featured per weekly email
STALE_DAYS = 45                    # past this (effective) a quote drops off the active list
_CLOSED = {"won", "dead"}          # statuses that are no longer "open"


# ── CSV parsing (reuse the proven engine parser via a temp file) ────────────────

def _parse(csv_text: str):
    """Return (rows, meta) where rows = list of dicts with quote/value/days/status.
    Reuses the Quote Revive engine's loader so the format stays in lockstep."""
    from products.quote_revive.quote_revive_engine import load_path
    tmp = Path(tempfile.gettempdir()) / f"_qrweekly_{os.getpid()}_{int(time.time()*1000)}.csv"
    try:
        tmp.write_text(csv_text, encoding="utf-8")
        df, meta = load_path(tmp)
    finally:
        try: tmp.unlink()
        except OSError: pass
    if df is None:
        return [], (meta or {})
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "quote": str(r["Quote"]).strip(),
            "detail": str(r["Detail"]).strip(),
            "value_num": float(r["ValueNum"]),
            "days": int(r["DaysNum"]),
            "followups": str(r["Followups"]).strip(),
            "status": str(r["StatusKey"]).strip().lower(),
        })
    return rows, (meta or {})


def _money(n: float) -> str:
    return f"${n:,.0f}"


# ── Weekly cadence logic ────────────────────────────────────────────────────────

_TOUCHES = [
    # (max_effective_days, touch_no, label, channel, goal)
    (4,   1, "Gentle check-in",  "Text",         "confirm they got it, stay warm, zero pressure"),
    (10,  2, "Value nudge",      "Email",        "remind them why now — light urgency, a reason to act"),
    (21,  3, "The decision ask", "Text + Email", "the friendly yes / no / not-yet that forces a reply"),
    (9999, 4, "Reactivation",    "Email",        "a second look at a quote that went quiet — no hard sell"),
]


def _touch_for(eff_days: int):
    for max_days, no, label, channel, goal in _TOUCHES:
        if eff_days <= max_days:
            return no, label, channel, goal
    return _TOUCHES[-1][1:]


def build_digest(csv_text: str, name: str, weeks_elapsed: int, now: int) -> Optional[dict]:
    """Build this week's chase list from a stored quote CSV. weeks_elapsed paces the
    follow-ups (each week ages every quote by 7 days, escalating its touch)."""
    rows, meta = _parse(csv_text)
    if not rows:
        return None

    biz = (meta.get("Business Name") or "your business").strip()
    owner = (meta.get("Owner Name") or name or "there").strip()

    # Age every quote by the weeks elapsed since the upload.
    for r in rows:
        r["eff_days"] = r["days"] + weeks_elapsed * 7

    open_rows = [r for r in rows if r["status"] not in _CLOSED]
    open_value = sum(r["value_num"] for r in open_rows)

    # This week's featured quotes: still in range, ranked by value (biggest first).
    active = [r for r in open_rows if r["eff_days"] <= STALE_DAYS]
    active.sort(key=lambda r: r["value_num"], reverse=True)
    featured = active[:MAX_ITEMS]
    for r in featured:
        no, label, channel, goal = _touch_for(r["eff_days"])
        r["touch_no"], r["touch_label"], r["channel"], r["goal"] = no, label, channel, goal

    # The one to call: biggest open opportunity overall (even if past the touch window).
    call = max(open_rows, key=lambda r: r["value_num"]) if open_rows else None

    messages = _write_messages(featured, biz, owner)
    for r, msg in zip(featured, messages):
        r["message"] = msg

    wk = datetime.fromtimestamp(now, tz=timezone.utc)
    return {
        "owner": owner,
        "biz": biz,
        "week_label": wk.strftime("Week of %B %-d, %Y"),
        "open_count": len(open_rows),
        "open_value": _money(open_value),
        "items": featured,
        "call": call,
    }


# ── Message generation (Claude when available; template fallback otherwise) ─────

def _template_message(r: dict, owner: str) -> str:
    """Deterministic, professional fallback message for a quote at its touch level.
    References the job + amount (the data carries no lead name), so it's sendable
    as-is — the owner can drop in the customer's first name if they want."""
    job = r["detail"] or r["quote"]
    amt = _money(r["value_num"])
    no = r["touch_no"]
    if no == 1:
        return (f"Quick note to make sure the quote for {job} ({amt}) reached you — "
                f"happy to answer any questions, no rush at all.")
    if no == 2:
        return (f"Following up on your {job} quote ({amt}). If it's still useful I can hold this "
                f"pricing and get you on the schedule — want me to?")
    if no == 3:
        return (f"I don't want to keep chasing if the timing's off — are we a yes, a no, or a "
                f"not-yet on the {job} quote ({amt})? Either way is totally fine, just let me know.")
    return (f"Circling back on your {job} quote ({amt}) — still on your radar? "
            f"If it's not the right time, no worries at all.")


def _write_messages(featured: list, biz: str, owner: str) -> list:
    if not featured:
        return []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return [_template_message(r, owner) for r in featured]
    try:
        import anthropic
        tool = {
            "name": "write_weekly_followups",
            "description": "Write one short follow-up message per quote, in order. Persistent but "
                           "professional; never pushy. The data has NO customer name — do not invent "
                           "one; open by referencing the job and amount. Match the touch level. "
                           "Plain text, no markdown.",
            "input_schema": {"type": "object", "properties": {"messages": {
                "type": "array", "items": {"type": "string"},
                "description": "One message per quote, same order as listed."}},
                "required": ["messages"]},
        }
        lines = []
        for i, r in enumerate(featured, 1):
            lines.append(f"{i}. \"{r['quote']}\" ({r['detail']}) — {_money(r['value_num'])}, "
                         f"{r['eff_days']} days cold. Touch {r['touch_no']} ({r['touch_label']}): {r['goal']}.")
        prompt = (f"Business: {biz}. Write this week's follow-up message for each open quote below — "
                  f"one per quote, matched to its touch level. Short, warm, professional, never pushy.\n\n"
                  + "\n".join(lines))
        c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = c.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=1200,
            system=("You are Quote Revive, EchoFrame's quote follow-up engine. You reactivate ghosted "
                    "quotes without burning the relationship. Persistent but professional. No markdown."),
            tools=[tool], tool_choice={"type": "tool", "name": "write_weekly_followups"},
            messages=[{"role": "user", "content": prompt}])
        for b in resp.content:
            if b.type == "tool_use":
                msgs = b.input.get("messages", [])
                if len(msgs) >= len(featured):
                    return [str(m) for m in msgs[:len(featured)]]
    except Exception:
        print(f"[QRWeekly] Claude messages failed, using templates:\n{traceback.format_exc()}", flush=True)
    return [_template_message(r, owner) for r in featured]


# ── Email rendering + send ──────────────────────────────────────────────────────

_DISCLAIMER = ('<p style="color:#9aa7b4;font-size:11px;margin-top:24px;">Business intelligence, not '
               'a sending tool — you send the messages. Informational only.</p>')


def render_email(d: dict) -> str:
    cards = []
    for r in d["items"]:
        msg = html.escape(r.get("message", "")).replace("\n", "<br>")
        cards.append(
            f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px 20px;margin-bottom:14px;">'
            f'<div style="font-size:13px;color:#94681C;font-weight:700;text-transform:uppercase;letter-spacing:.04em;">'
            f'{html.escape(r["channel"])} · {html.escape(r["touch_label"])}</div>'
            f'<div style="font-size:16px;font-weight:700;color:#0A274F;margin:4px 0 2px;">'
            f'{html.escape(r["quote"])} · {_money(r["value_num"])}</div>'
            f'<div style="font-size:13px;color:#6B7280;margin-bottom:10px;">{r["eff_days"]} days cold</div>'
            f'<div style="font-size:15px;color:#111827;line-height:1.55;background:#F9FAFB;border-radius:8px;padding:12px 14px;">'
            f'{msg}</div></div>')
    call_html = ""
    if d.get("call"):
        c = d["call"]
        call_html = (
            f'<div style="background:#0A274F;border-radius:12px;padding:18px 20px;margin:6px 0 18px;color:#fff;">'
            f'<div style="font-size:13px;color:#E0A93F;font-weight:700;text-transform:uppercase;letter-spacing:.04em;">'
            f'Call this one yourself</div>'
            f'<div style="font-size:16px;font-weight:700;margin:4px 0;">{html.escape(c["quote"])} · {_money(c["value_num"])}</div>'
            f'<div style="font-size:14px;color:#C7D2E0;">Your biggest open opportunity — a 2-minute call beats any text.</div></div>')
    intro = (f'<p style="font-size:15px;color:#4B5563;">Hi {html.escape(d["owner"])}, here are the quotes worth '
             f'chasing this week. Send these today — they\'re written and ready.</p>') if d["items"] else (
             f'<p style="font-size:15px;color:#4B5563;">Hi {html.escape(d["owner"])}, nothing urgent to chase this week. '
             f'Upload your latest open quotes anytime to keep this current.</p>')
    return (
        f'<div style="font-family:Inter,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:560px;margin:0 auto;">'
        f'<div style="font-size:12px;color:#94681C;font-weight:700;text-transform:uppercase;letter-spacing:.06em;">'
        f'Quote Revive · {html.escape(d["week_label"])}</div>'
        f'<h2 style="font-size:22px;color:#0A274F;margin:6px 0 14px;">This week\'s chase list</h2>'
        f'{intro}{call_html}{"".join(cards)}'
        f'<p style="font-size:13px;color:#6B7280;margin-top:8px;">{d["open_count"]} open quotes · {d["open_value"]} on the table. '
        f'Added new quotes? Drop them in anytime to keep next week sharp.</p>{_DISCLAIMER}</div>')


def send_digest(to_email: str, d: dict) -> None:
    import resend
    resend.api_key = os.environ.get("RESEND_API_KEY", "")
    subject = (f"This week's chase list — {len(d['items'])} quote{'s' if len(d['items']) != 1 else ''} to follow up"
               if d["items"] else "Quote Revive — nothing urgent this week")
    resend.Emails.send({
        "from": os.environ.get("EMAIL_FROM", "EchoFrame <jacob.starling@echoframe.net>"),
        "to": [to_email], "subject": subject, "html": render_email(d)})


# ── Weekly run (called by the cron endpoint) ────────────────────────────────────

def send_first_digest(email: str, csv_text: str, name: str, now: int) -> None:
    """Send the customer their first chase list right after they upload — instant
    value — then the weekly cron takes over. No-ops cleanly if there's nothing to chase."""
    try:
        digest = build_digest(csv_text, name, 0, int(now))
        if digest and digest.get("items"):
            send_digest(email, digest)
            print("[QRWeekly] First digest sent on upload.")
        else:
            print("[QRWeekly] Upload had no open quotes — no first digest.")
    except Exception:
        print(f"[QRWeekly] First-digest ERROR:\n{traceback.format_exc()}", flush=True)


def run_weekly(*, _now: Optional[int] = None) -> dict:
    now = int(_now if _now is not None else time.time())
    summary = {"checked": 0, "sent": 0, "skipped": 0, "errors": 0}
    for safe in store.list_qr_subscribers():
        summary["checked"] += 1
        try:
            data = store.load_quote_data(safe)
            if not data or not data.get("csv") or not data.get("email"):
                summary["skipped"] += 1
                continue
            weeks = max(0, (now - int(data.get("uploaded_at", now))) // WEEK)
            digest = build_digest(data["csv"], data.get("name", "there"), weeks, now)
            # Only email when there's actually something to chase — no weekly "nothing" noise.
            if not digest or not digest.get("items"):
                summary["skipped"] += 1
                continue
            send_digest(data["email"], digest)
            summary["sent"] += 1
            print(f"[QRWeekly] Digest sent (items={len(digest['items'])}, week={weeks}).")  # no PII
        except Exception:
            summary["errors"] += 1
            print(f"[QRWeekly] ERROR:\n{traceback.format_exc()}", flush=True)
    print(f"[QRWeekly] Weekly run complete: {summary}")
    return summary
