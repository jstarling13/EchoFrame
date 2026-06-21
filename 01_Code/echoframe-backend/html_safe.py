"""
EchoFrame — HTML sanitizer for model-written report fields (QA finding E-2).

Report templates render the AI narrative with a `clean` Jinja filter instead of
`safe`. The narrative is produced from a prompt seeded with un-escaped CSV content
(business name, quote/line-item text), so a malicious cell like
``<img src=x onerror=alert(1)>`` could otherwise ride into the delivered HTML
report. `clean()` allows only the handful of inline tags the reports actually use
and strips everything else.

bleach is optional: if it isn't installed, we fall back to full HTML-escaping —
safe (no active markup can render), just without the bold/dollar formatting. So a
missing dependency degrades gracefully and never breaks report generation.
"""

from __future__ import annotations

from markupsafe import Markup, escape

try:
    import bleach
    _HAS_BLEACH = True
except Exception:  # pragma: no cover - exercised only when bleach isn't installed
    _HAS_BLEACH = False

# The ONLY tags the report narratives use — inline emphasis + the dollar/highlight spans.
_ALLOWED_TAGS = ["b", "strong", "i", "em", "u", "span", "br", "sup", "sub"]
_ALLOWED_ATTRS = {"span": ["class"]}


def clean(value):
    """Sanitize a model-written HTML string to the report's inline-tag allow-list and
    return it as Markup (so Jinja renders it raw, like `safe`, but cleaned). Falls back
    to full escaping when bleach is unavailable. Never raises."""
    s = "" if value is None else str(value)
    try:
        if _HAS_BLEACH:
            return Markup(bleach.clean(s, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True))
    except Exception:
        pass
    return escape(s)
