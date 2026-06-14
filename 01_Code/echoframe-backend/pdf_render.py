"""
HTML → PDF rendering via headless Chromium (Playwright).

Renders the report HTML exactly as Chrome would, then prints it to PDF — so the
PDF is pixel-identical to the browser view the reports were designed for.

Setup (local + Railway):
    pip install playwright
    playwright install chromium        # downloads the headless browser

On Railway, add a build/post-install step:  playwright install --with-deps chromium

Raises RuntimeError if Playwright/Chromium isn't available, so callers can fall
back to attaching the HTML file instead of crashing.
"""
from __future__ import annotations

import base64


def html_to_pdf(html, *, fmt: str = "Letter") -> bytes:
    """Render a full HTML document (bytes or str) to PDF bytes."""
    if isinstance(html, (bytes, bytearray)):
        html = bytes(html).decode("utf-8", "replace")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # not installed
        raise RuntimeError(f"Playwright unavailable: {e}") from e

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        try:
            page = browser.new_page()
            # Load the self-contained report and wait for webfonts to settle.
            page.set_content(html, wait_until="networkidle")
            try:
                page.evaluate("document.fonts && document.fonts.ready")
            except Exception:
                pass
            # Use the report's print stylesheet (it's designed as 8.5x11 pages).
            page.emulate_media(media="print")
            pdf = page.pdf(
                format=fmt,
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()
    return pdf


def report_attachment(html_bytes, html_filename: str) -> dict:
    """Build a Resend attachment dict from a report's HTML bytes.

    Returns a PDF attachment when headless Chromium is available (renders
    identically for every recipient, can't be mis-opened in Word); falls back to
    the HTML file otherwise. `html_filename` is the intended .html name — the
    extension is swapped to .pdf automatically.
    """
    stem = html_filename[:-5] if html_filename.lower().endswith(".html") else html_filename
    try:
        pdf = html_to_pdf(html_bytes)
        return {
            "filename": f"{stem}.pdf",
            "content": base64.b64encode(pdf).decode("ascii"),
            "content_type": "application/pdf",
        }
    except Exception as e:
        print(f"[pdf_render] PDF unavailable ({e}); attaching HTML instead.")
        return {
            "filename": f"{stem}.html",
            "content": base64.b64encode(html_bytes if isinstance(html_bytes, (bytes, bytearray)) else str(html_bytes).encode()).decode("ascii"),
            "content_type": "text/html",
        }


def docx_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert a .docx (bytes) to PDF (bytes) via headless LibreOffice.

    Setup:
      - macOS:          brew install --cask libreoffice
      - Debian/Railway: apt-get install -y libreoffice  (or a libreoffice build pack)
    Raises RuntimeError if LibreOffice isn't found or the conversion fails, so the
    caller can fall back to sending the original .docx.
    """
    import os
    import shutil
    import subprocess
    import tempfile

    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/opt/homebrew/bin/soffice",
    ]
    soffice = next((c for c in candidates if c and os.path.exists(c)), None)
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found")

    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "report.docx")
        with open(src, "wb") as fh:
            fh.write(docx_bytes)
        proc = subprocess.run(
            [
                soffice, "--headless", "--norestore",
                f"-env:UserInstallation=file://{os.path.join(d, 'lo_profile')}",
                "--convert-to", "pdf", "--outdir", d, src,
            ],
            capture_output=True, timeout=180,
        )
        pdf_path = os.path.join(d, "report.pdf")
        if not os.path.exists(pdf_path):
            raise RuntimeError(
                f"LibreOffice conversion failed (rc={proc.returncode}): "
                f"{proc.stderr.decode('utf-8', 'replace')[:300]}"
            )
        with open(pdf_path, "rb") as fh:
            return fh.read()
