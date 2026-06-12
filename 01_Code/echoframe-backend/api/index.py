"""
Vercel Python serverless entrypoint.
─────────────────────────────────────────────────────────────────────────────
Vercel's @vercel/python runtime serves the ASGI `app` exported here. All routing
is handled by FastAPI itself (vercel.json rewrites every path to this function).

The backend package lives one directory up, so we add it to sys.path before
importing main. ECHOFRAME_UPLOADS_DIR / ECHOFRAME_REPORTS_DIR are pointed at the
function's only writable location (/tmp) — set them as project env vars, or rely
on the defaults below if unset.
"""

import os
import sys
from pathlib import Path

# Make the backend root importable (main.py, registry.py, products/, …).
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Only /tmp is writable on Vercel. Default the write-paths there if not provided.
os.environ.setdefault("ECHOFRAME_UPLOADS_DIR", "/tmp/echoframe/uploads")
os.environ.setdefault("ECHOFRAME_REPORTS_DIR", "/tmp/echoframe/reports")

from main import app  # noqa: E402  (must follow sys.path / env setup)

# Vercel's ASGI handler picks up this module-level `app`.
__all__ = ["app"]
