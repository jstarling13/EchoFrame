"""
EchoFrame durable key/value + set store
─────────────────────────────────────────────────────────────────────────────
On Vercel the local filesystem does NOT persist between serverless invocations,
so anything that must outlive a single request (the customer directory, the
per-billing-period upload state, and the webhook idempotency keys) lives here.

Backend selection (decided once at import):
  • If Upstash Redis REST credentials are present in the environment
    (KV_REST_API_URL / KV_REST_API_TOKEN  — the names Vercel's Upstash
    Marketplace integration injects — or the UPSTASH_REDIS_REST_* equivalents),
    every operation is a single HTTPS call to the Upstash REST API.
  • Otherwise we fall back to an in-process dict. That keeps local dev, the
    demos, and the test-suite working with zero configuration. The fallback is
    NOT durable across processes — never rely on it in production.

Only the small JSON records and idempotency keys go here. Uploaded CSVs and the
generated reports are transient and stay on the function's /tmp disk for the
life of the request (see ECHOFRAME_UPLOADS_DIR / ECHOFRAME_REPORTS_DIR).
"""

from __future__ import annotations

import os
import json
import time
import threading
from typing import Optional

import httpx

# ── Backend detection ──────────────────────────────────────────────────────────

_REST_URL = (
    os.environ.get("KV_REST_API_URL")
    or os.environ.get("UPSTASH_REDIS_REST_URL")
    or ""
).rstrip("/")
_REST_TOKEN = (
    os.environ.get("KV_REST_API_TOKEN")
    or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    or ""
)


def is_configured() -> bool:
    """True when a durable (Upstash Redis) backend is available."""
    return bool(_REST_URL and _REST_TOKEN)


# ── In-memory fallback (dev / test only) ───────────────────────────────────────
# A tiny thread-safe store that mimics the handful of Redis commands we use.
# Expiries are honoured lazily so TTL-based idempotency behaves the same way.

_lock = threading.Lock()
_mem: dict[str, tuple[str, Optional[float]]] = {}   # key -> (value, expires_at|None)
_mem_sets: dict[str, set[str]] = {}


def _mem_expired(key: str) -> bool:
    item = _mem.get(key)
    if item is None:
        return True
    _, exp = item
    if exp is not None and exp <= time.time():
        _mem.pop(key, None)
        return True
    return False


# ── Upstash REST transport ─────────────────────────────────────────────────────

def _rest(command: list) -> object:
    """Execute a single Redis command via the Upstash REST API; return `result`."""
    resp = httpx.post(
        _REST_URL,
        headers={"Authorization": f"Bearer {_REST_TOKEN}"},
        json=command,
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json().get("result")


# ── Public string ops ──────────────────────────────────────────────────────────

def kv_get(key: str) -> Optional[str]:
    if is_configured():
        result = _rest(["GET", key])
        return result if result is not None else None
    with _lock:
        if _mem_expired(key):
            return None
        return _mem[key][0]


def kv_set(key: str, value: str, ex: Optional[int] = None) -> None:
    if is_configured():
        cmd = ["SET", key, value]
        if ex:
            cmd += ["EX", str(int(ex))]
        _rest(cmd)
        return
    with _lock:
        _mem[key] = (value, time.time() + ex if ex else None)


def kv_setnx(key: str, value: str, ex: Optional[int] = None) -> bool:
    """Atomic set-if-absent. Returns True if WE created the key (first time),
    False if it already existed. Used for webhook idempotency."""
    if is_configured():
        cmd = ["SET", key, value, "NX"]
        if ex:
            cmd += ["EX", str(int(ex))]
        # Upstash returns "OK" when the key was set, null when NX prevented it.
        return _rest(cmd) == "OK"
    with _lock:
        if not _mem_expired(key):
            return False
        _mem[key] = (value, time.time() + ex if ex else None)
        return True


def kv_delete(key: str) -> None:
    if is_configured():
        _rest(["DEL", key])
        return
    with _lock:
        _mem.pop(key, None)


# ── Public set ops (used to enumerate pending billing periods) ─────────────────

def set_add(set_key: str, member: str) -> None:
    if is_configured():
        _rest(["SADD", set_key, member])
        return
    with _lock:
        _mem_sets.setdefault(set_key, set()).add(member)


def set_remove(set_key: str, member: str) -> None:
    if is_configured():
        _rest(["SREM", set_key, member])
        return
    with _lock:
        _mem_sets.get(set_key, set()).discard(member)


def set_members(set_key: str) -> list[str]:
    if is_configured():
        result = _rest(["SMEMBERS", set_key])
        return list(result or [])
    with _lock:
        return list(_mem_sets.get(set_key, set()))


# ── JSON convenience ───────────────────────────────────────────────────────────

def get_json(key: str) -> Optional[dict]:
    raw = kv_get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def set_json(key: str, value: dict, ex: Optional[int] = None) -> None:
    kv_set(key, json.dumps(value), ex=ex)


# ── Domain helpers ─────────────────────────────────────────────────────────────
# Key namespaces are prefixed so they never collide with other Upstash users.

_CUSTOMER_PREFIX = "ef:customer:"        # ef:customer:<safe_email> -> {name, stripe_customer, ...}
_PERIOD_PREFIX   = "ef:period:"          # ef:period:<safe_email>:<period> -> billing/upload record
_PENDING_SET     = "ef:pending_periods"  # set of "<safe_email>:<period>" awaiting upload
_EVENT_PREFIX    = "ef:evt:"             # ef:evt:<event_id> -> "1" (idempotency, TTL'd)

# How long processed-event markers live. Comfortably longer than Stripe's
# ~3-day automatic retry window so replays after a restart are still caught.
EVENT_TTL_SECONDS = 7 * 24 * 3600
# How long a period record / pending marker lives before self-cleaning.
PERIOD_TTL_SECONDS = 45 * 24 * 3600


def claim_event(event_id: str) -> bool:
    """Durable, atomic idempotency claim. True = first time we've seen this
    event (caller should process it); False = duplicate (caller should skip).
    Only meaningful when a durable backend is configured."""
    return kv_setnx(f"{_EVENT_PREFIX}{event_id}", "1", ex=EVENT_TTL_SECONDS)


def save_customer_record(safe_email: str, record: dict) -> None:
    existing = get_json(f"{_CUSTOMER_PREFIX}{safe_email}") or {}
    existing.update({k: v for k, v in record.items() if v not in (None, "")})
    set_json(f"{_CUSTOMER_PREFIX}{safe_email}", existing)


def load_customer_record(safe_email: str) -> Optional[dict]:
    return get_json(f"{_CUSTOMER_PREFIX}{safe_email}")


def _period_key(safe_email: str, period: str) -> str:
    return f"{_PERIOD_PREFIX}{safe_email}:{period}"


def save_period(safe_email: str, period: str, record: dict) -> None:
    set_json(_period_key(safe_email, period), record, ex=PERIOD_TTL_SECONDS)


def load_period(safe_email: str, period: str) -> Optional[dict]:
    return get_json(_period_key(safe_email, period))


def mark_period_billed(safe_email: str, period: str, record: dict) -> None:
    """Record that a billing period was charged and is awaiting an upload."""
    save_period(safe_email, period, record)
    set_add(_PENDING_SET, f"{safe_email}:{period}")


def mark_period_uploaded(safe_email: str, period: str) -> None:
    """Mark the period's files as received; drop it from the pending set."""
    rec = load_period(safe_email, period) or {}
    rec["uploaded"] = True
    rec["uploaded_at"] = int(time.time())
    save_period(safe_email, period, rec)
    set_remove(_PENDING_SET, f"{safe_email}:{period}")


def list_pending_periods() -> list[tuple[str, str]]:
    """Return [(safe_email, period), ...] for every period still awaiting an upload."""
    out = []
    for member in set_members(_PENDING_SET):
        safe_email, _, period = member.partition(":")
        if safe_email and period:
            out.append((safe_email, period))
    return out
