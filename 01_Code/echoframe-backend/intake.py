"""
EchoFrame — Free First Look intake (public lead capture)
─────────────────────────────────────────────────────────────────────────────
The public "Free First Look" page (site/sample.html) is a pre-purchase lead
form, not a paid product upload — a visitor who isn't sure what they need yet.
This module is deliberately separate from the paid `/api/upload` flow in
main.py: leads are not customers, don't have a Stripe session, and don't run
a report engine. They get their own namespace, TTL, and dedup window in
store.py (see save_lead / claim_lead_dedup) rather than reusing the customer/
period records built for billing.

Contract (matches the frontend's intake/api-adapter.js exactly):
  POST multipart/form-data
    lead:  JSON blob — {area, product, source, business, problem, contact,
                         fileMetadata, createdAt}
    files: 0-3 uploaded files (optional; supporting documents only)

  Success  200 {"status":"success","reference":"EF-...","message":"..."}
  Bad input   422 {"category":"validation","safe_message":"...","field_errors":{...}}
  Duplicate   409 {"category":"duplicate_submission","safe_message":"...","existing_reference":"..."}
  Server error 500 {"category":"server_rejection","safe_message":"...","error_reference":"..."}

Deliberately NOT duplicated here: the detailed per-product metadata (accepted
extensions, required columns, price, etc.) that already lives in the frontend's
intake/product-config.js. This module treats `product` as a labeled string for
the lead record and validates only `area` against a fixed allowlist — one
source of truth for the catalog, per EXISTING_SYSTEMS_NOT_TO_REPLACE.md.

review_gate does not apply here: that gate holds a generated REPORT for human
approval before it reaches a paying customer. A lead has no report to hold —
the "human review" for a lead is Jacob reading the owner-alert email and
replying, which is the point of this whole flow.
"""

from __future__ import annotations

import os
import re
import json
import time
import html
import base64
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

import store
import emails

# ── Config ──────────────────────────────────────────────────────────────────

MAX_INTAKE_FILES = 3
MAX_INTAKE_FILE_BYTES = 20 * 1024 * 1024  # 20 MB — the highest per-product ceiling in product-config.js
ALLOWED_INTAKE_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".docx"}
ALLOWED_AREAS = {"intelligence", "revenue", "ops", "partners", "general"}

# Mirrors intake/intake-config.js's INTAKE_CONFIG.areas labels (kept as a small,
# display-only lookup here — not the product catalog itself).
_AREA_LABELS = {
    "intelligence": "Intelligence",
    "revenue": "Revenue",
    "ops": "Operations",
    "partners": "Partners",
    "general": "General guidance",
}

# Mirrors main.py's pattern exactly (portal.py does the same) so the same
# address normalises to the same store key everywhere.
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,}$')
_SAFE_CHAR_RE = re.compile(r'[^a-zA-Z0-9_+\-]')


def _safe_email(email: str) -> str:
    email = email.strip().lower()
    local, _, domain = email.partition("@")
    return f"{_SAFE_CHAR_RE.sub('_', local)}_at_{_SAFE_CHAR_RE.sub('_', domain)}"


def _fail(status: int, category: str, safe_message: str, **extra) -> JSONResponse:
    body = {"category": category, "safe_message": safe_message, "error_reference": _reference()}
    body.update(extra)
    return JSONResponse(body, status_code=status)


def _reference() -> str:
    # Matches the frontend's own dev-mode mock format (EF-########) so a lead
    # created in either place looks the same to a human reading it later.
    return f"EF-{str(int(time.time() * 1000))[-8:]}"


def _esc(v) -> str:
    return html.escape(str(v or ""))


async def _read_lead_json(form) -> dict | None:
    """The 'lead' field arrives as a Blob (application/json), which Starlette
    exposes as an UploadFile-like part. Handle that or a plain string field."""
    part = form.get("lead")
    if part is None:
        return None
    if hasattr(part, "read"):
        raw = await part.read()
    else:
        raw = part
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _validate(lead: dict) -> dict:
    """Return {field: message} for anything missing/invalid. Mirrors
    intake/validation.js's server-authoritative counterpart — the client
    already checked this, but the server is the one that must be trusted."""
    errors: dict[str, str] = {}

    area = (lead.get("area") or "").strip()
    if area not in ALLOWED_AREAS:
        errors["area"] = "Choose a valid starting point."

    contact = lead.get("contact") or {}
    if not (contact.get("name") or "").strip():
        errors["name"] = "Enter your full name."
    email = (contact.get("email") or "").strip().lower()
    if not _EMAIL_RE.match(email):
        errors["email"] = "Enter a valid business email."
    if not contact.get("operationalConsent"):
        errors["operationalConsent"] = "Permission is required so we can respond."

    problem = lead.get("problem") or {}
    if not (problem.get("summary") or "").strip():
        errors["summary"] = "Tell us what is happening."

    return errors


async def _handle_intake(request: Request) -> JSONResponse:
    try:
        form = await request.form()
    except Exception:
        return _fail(400, "validation", "We could not read that submission. Please try again.")

    lead = await _read_lead_json(form)
    if lead is None:
        return _fail(400, "validation", "We could not read that submission. Please try again.")

    field_errors = _validate(lead)
    if field_errors:
        return _fail(422, "validation", "Please review the highlighted information.",
                     field_errors=field_errors)

    area = (lead.get("area") or "general").strip()
    product = (lead.get("product") or "general").strip()[:64] or "general"
    source = (lead.get("source") or "direct").strip()[:64] or "direct"
    contact = lead.get("contact") or {}
    business = lead.get("business") or {}
    problem = lead.get("problem") or {}
    email = contact.get("email", "").strip().lower()
    safe_email = _safe_email(email)

    # ── Files: server is the validation authority, not the browser ──────────
    raw_files = form.getlist("files")
    if len(raw_files) > MAX_INTAKE_FILES:
        return _fail(422, "validation", f"Attach at most {MAX_INTAKE_FILES} files.")

    attachments = []
    for f in raw_files:
        filename = getattr(f, "filename", "") or "upload"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_INTAKE_EXTENSIONS:
            return _fail(422, "unsupported_file",
                         f"Use one of: {', '.join(sorted(ALLOWED_INTAKE_EXTENSIONS))}")
        content = await f.read(MAX_INTAKE_FILE_BYTES + 1)
        if len(content) > MAX_INTAKE_FILE_BYTES:
            return _fail(422, "file_too_large",
                         f"Each file must be {MAX_INTAKE_FILE_BYTES // (1024 * 1024)} MB or smaller.")
        content_type = getattr(f, "content_type", None) or "application/octet-stream"
        attachments.append({
            "filename": filename,
            "content": base64.b64encode(content).decode("ascii"),
            "content_type": content_type,
        })

    # ── Duplicate submission guard (double-click / retry, not a new inquiry) ─
    reference = _reference()
    is_first, reference = store.claim_lead_dedup(safe_email, area, product, reference)
    if not is_first:
        return _fail(409, "duplicate_submission",
                     "Looks like we already have this request — no need to send it twice.",
                     existing_reference=reference)

    # ── Persist the lead (Redis via store.py; see LEAD_TTL_SECONDS) ──────────
    record = {
        "reference": reference,
        "area": area,
        "product": product,
        "source": source,
        "business": business,
        "problem": problem,
        "contact": {
            "name": contact.get("name", ""),
            "email": email,
            "phone": contact.get("phone", ""),
            "preferred": contact.get("preferred", ""),
            "operationalConsent": bool(contact.get("operationalConsent")),
            "marketingConsent": bool(contact.get("marketingConsent")),
        },
        "fileMetadata": [{"type": a["content_type"], "size": len(a["content"])} for a in attachments],
        "createdAt": lead.get("createdAt") or int(time.time() * 1000),
        "status": "new",
    }
    try:
        store.save_lead(reference, record)
    except Exception:
        print(f"[intake] WARN: save_lead failed:\n{traceback.format_exc()}", flush=True)

    area_label = _AREA_LABELS.get(area, area.title())
    product_name = product.replace("_", " ").title()

    # ── Notify (best-effort — a delivery hiccup must not fail the submission) ─
    try:
        emails.send_intake_confirmation(
            to_email=email,
            name=contact.get("name", ""),
            reference=reference,
            area_label=area_label,
            product_name=product_name,
            file_count=len(attachments),
        )
    except Exception:
        print(f"[intake] WARN: customer confirmation email failed:\n{traceback.format_exc()}", flush=True)

    try:
        emails.send_intake_owner_alert(
            reference=reference,
            area_label=area_label,
            product_name=product_name,
            business_name=_esc(business.get("businessName", "")),
            contact_name=_esc(contact.get("name", "")),
            contact_email=email,
            contact_phone=_esc(contact.get("phone", "")),
            summary=_esc(problem.get("summary", "")),
            attachments=attachments or None,
        )
    except Exception:
        print(f"[intake] WARN: owner alert email failed:\n{traceback.format_exc()}", flush=True)

    print(f"[intake] lead received: {reference} area={area} product={product}", flush=True)
    return JSONResponse({
        "status": "success",
        "reference": reference,
        "message": "Your first look has been received",
    })


def register_intake(app, limiter) -> None:
    """Mount the intake route, reusing the app's rate limiter (same pattern as
    portal.register_portal) to blunt abuse without a circular import."""
    app.add_api_route(
        "/api/intake",
        limiter.limit("5/minute")(_handle_intake),
        methods=["POST"],
        response_model=None,
    )
