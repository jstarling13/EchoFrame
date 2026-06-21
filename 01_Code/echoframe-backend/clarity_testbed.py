"""
Clarity Report — LOCAL TEST BENCH (dev only, not wired into production)
======================================================================
A throwaway page for stress-testing the Clarity engine against very messy
data. It runs the REAL pipeline (same parse + math + charts + DOCX build),
but:

  • NO Stripe gate    — just paste/upload and go
  • NO email send     — we call the engine internals, never _send_report_email
  • SHOWS the parse   — you see exactly how each messy row was interpreted
                        (raw value -> coerced number), which is where bad data
                        actually breaks, plus computed metrics, leaks, and any
                        traceback instead of a blank 500.

Run:
    cd 01_Code/echoframe-backend
    .venv/bin/python -m uvicorn clarity_testbed:app --reload --port 8011
Then open http://127.0.0.1:8011/

A "fast (skip LLM)" toggle lets you iterate on parsing without spending an
Anthropic call; untick it to exercise the full narrative + DOCX download.
"""
from __future__ import annotations

import html
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from products.clarity import clarity_engine as ce  # noqa: E402

TEST_EMAIL = "testbench+clarity@echoframe.local"

app = FastAPI(title="Clarity Test Bench")


# A deliberately messy (but single-period) starter sample so there's something
# to mangle immediately. Single-period = 2 columns throughout, which the engine's
# pd.read_csv can actually load. NOTE: adding a third "Prior" column to any row
# below crashes _load_financials (pandas locks the column count to the first,
# 2-col metadata row) — a real engine bug; try it to reproduce.
SAMPLE_CSV = """_Business Name,Reliable Heating & Air
_Industry,HVAC
_Location,"Columbus, OH"
_Month,May 2026
_Owner Name,Dana
Revenue,"$128,400"
Cost of Goods Sold,52100
Payroll,"$38,000"
Rent,4500
Marketing,nan
Software & Subscriptions,"1,250"
Owner Draw,
Miscellaneous,—
"""


def _esc(x) -> str:
    return html.escape(str(x))


def _page(body: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Clarity — Test Bench</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 980px;
         margin: 0 auto; padding: 28px 20px 80px; color: #14233f; }}
  h1 {{ color: #0a274f; margin-bottom: 2px; }}
  .sub {{ color: #5a6b85; margin-top: 0; font-size: 14px; }}
  .card {{ background: #f6f8fc; border: 1px solid #dde4f0; border-radius: 10px;
          padding: 16px 18px; margin: 16px 0; }}
  label {{ display:block; font-weight:600; font-size:13px; margin:10px 0 4px; }}
  input[type=text] {{ width: 100%; padding: 8px 10px; border:1px solid #c5d0e2;
          border-radius:6px; font-size:14px; box-sizing:border-box; }}
  textarea {{ width:100%; min-height:230px; font-family: ui-monospace, Menlo, monospace;
          font-size:13px; padding:10px; border:1px solid #c5d0e2; border-radius:6px;
          box-sizing:border-box; }}
  .row {{ display:flex; gap:14px; flex-wrap:wrap; }}
  .row > div {{ flex:1; min-width:180px; }}
  button {{ background:#0a274f; color:#fff; border:0; border-radius:8px;
          padding:11px 22px; font-size:15px; font-weight:600; cursor:pointer; margin-top:14px; }}
  table {{ border-collapse: collapse; width:100%; font-size:13px; margin-top:8px; }}
  th, td {{ border:1px solid #dde4f0; padding:6px 9px; text-align:left; }}
  th {{ background:#eef2f9; }}
  td.num {{ text-align:right; font-variant-numeric: tabular-nums; }}
  .warn {{ color:#a3331f; }} .ok {{ color:#1d7a46; }}
  pre {{ background:#13233f; color:#e8eefc; padding:14px; border-radius:8px;
         overflow:auto; font-size:12.5px; }}
  .pill {{ display:inline-block; background:#0a274f; color:#fff; font-size:11px;
         padding:2px 8px; border-radius:20px; margin-left:8px; vertical-align:middle; }}
  a.dl {{ display:inline-block; margin-top:12px; }}
</style></head><body>{body}</body></html>"""


FORM = """
<h1>Clarity Report — Test Bench <span class="pill">DEV · no Stripe · no email</span></h1>
<p class="sub">Throw messy data at the real engine and see exactly how it parses, computes, and copes.</p>
<form method="post" action="/run" enctype="multipart/form-data">
  <div class="card">
    <div class="row">
      <div><label>Business name</label><input type="text" name="business" value="Reliable Heating &amp; Air"></div>
      <div><label>Industry</label><input type="text" name="industry" value="HVAC"></div>
    </div>
    <div class="row">
      <div><label>Location</label><input type="text" name="location" value="Columbus, OH"></div>
      <div><label>Month</label><input type="text" name="month" value="May 2026"></div>
    </div>
    <label>CSV — paste messy data here (or upload a file below)</label>
    <textarea name="csv_text">__SAMPLE__</textarea>
    <label>…or upload a .csv (overrides the textarea)</label>
    <input type="file" name="file" accept=".csv,text/csv,text/plain">
    <label style="font-weight:500; margin-top:14px;">
      <input type="checkbox" name="skip_llm" value="1" checked>
      Fast mode — skip the LLM narrative + DOCX (parse &amp; metrics only). Untick for a full run + downloadable report.
    </label>
    <button type="submit">Run the engine →</button>
  </div>
</form>
""".replace("__SAMPLE__", _esc(SAMPLE_CSV))


@app.get("/", response_class=HTMLResponse)
async def home():
    return _page(FORM)


@app.get("/sample", response_class=PlainTextResponse)
async def sample():
    return SAMPLE_CSV


def _meta_lines(business: str, industry: str, location: str, month: str) -> str:
    """Mirror main.py's intake-field injection: prepend _Key,value rows so the
    typed form fields personalize the report exactly like the real upload does."""
    out = []
    for key, val in (("Business Name", business), ("Industry", industry),
                     ("Location", location), ("Month", month)):
        v = (val or "").strip()
        if not v:
            continue
        if ("," in v) or ('"' in v) or ("\n" in v):
            v = '"' + v.replace('"', '""') + '"'
        out.append(f"_{key},{v}")
    return ("\n".join(out) + "\n") if out else ""


@app.post("/run", response_class=HTMLResponse)
async def run(
    business: str = Form(""),
    industry: str = Form(""),
    location: str = Form(""),
    month: str = Form(""),
    csv_text: str = Form(""),
    skip_llm: str = Form(""),
    file: UploadFile | None = File(None),
):
    # 1 — assemble the CSV exactly as the real /api/upload would (form meta on top)
    if file is not None and file.filename:
        body = (await file.read()).decode("utf-8", errors="replace")
    else:
        body = csv_text
    raw = _meta_lines(business, industry, location, month) + body

    ce.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    dest = ce.UPLOADS_DIR / f"{ce._safe_email(TEST_EMAIL)}.csv"
    dest.write_text(raw, encoding="utf-8")

    sections: list[str] = ["<a href='/'>&larr; back</a><h1>Clarity — run result</h1>"]

    # 2 — parse (the messiest step; surface raw -> coerced)
    try:
        df, meta = ce._load_financials(TEST_EMAIL)
    except Exception:
        return _page("".join(sections) + _err("CSV parse (_load_financials) blew up", raw))
    if df is None:
        return _page("".join(sections) + "<p class='warn'>No CSV found / unreadable.</p>")

    sections.append(_meta_table(meta))
    sections.append(_parse_table(df, body))

    # 3 — benchmarks + metrics
    try:
        benchmarks = ce._get_benchmarks(meta.get("Industry", ""))
        metrics = ce._calculate_metrics(df, meta, benchmarks)
    except Exception:
        return _page("".join(sections) + _err("Metrics (_calculate_metrics) blew up", raw))
    sections.append(_dict_block("Computed metrics", metrics))

    # 4 — leaks
    try:
        leaks = ce._identify_leaks(metrics)
        sections.append(_dict_block(f"Identified leaks ({len(leaks)})", {"leaks": leaks}))
    except Exception:
        sections.append(_err("Leak detection (_identify_leaks) blew up", raw, fatal=False))
        leaks = []

    if skip_llm == "1":
        sections.append("<div class='card'><b class='ok'>Fast mode.</b> Parse + metrics only — "
                        "untick “Fast mode” to run the LLM narrative and download the DOCX.</div>")
        return _page("".join(sections))

    # 5 — full run: narrative + DOCX (real Anthropic call)
    try:
        prose = ce._generate_narrative(meta, metrics, leaks)
        sections.append(_dict_block("LLM narrative", prose))
    except Exception:
        return _page("".join(sections) + _err("Narrative (_generate_narrative) blew up", raw))

    try:
        docx_bytes = ce._build_docx(meta, metrics, leaks, prose)
        path = ce._save_report(TEST_EMAIL, docx_bytes, meta)
        name = Path(path).name
        sections.append(
            f"<div class='card'><b class='ok'>Report built — {len(docx_bytes):,} bytes.</b><br>"
            f"<a class='dl' href='/report/{_esc(name)}'>⬇ download {_esc(name)}</a></div>")
    except Exception:
        return _page("".join(sections) + _err("DOCX build (_build_docx) blew up", raw))

    return _page("".join(sections))


@app.get("/report/{name}")
async def report(name: str):
    safe = Path(name).name  # strip any path components
    path = ce.REPORTS_DIR / safe
    if not path.exists():
        return PlainTextResponse("not found", status_code=404)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe,
    )


# ── render helpers ────────────────────────────────────────────────────────────

def _err(title: str, raw: str, fatal: bool = True) -> str:
    tb = traceback.format_exc()
    tag = "FATAL" if fatal else "non-fatal"
    return (f"<div class='card'><b class='warn'>{_esc(title)} [{tag}]</b>"
            f"<pre>{_esc(tb)}</pre></div>")


def _meta_table(meta: dict) -> str:
    rows = "".join(f"<tr><th>{_esc(k)}</th><td>{_esc(v)}</td></tr>" for k, v in meta.items())
    return f"<div class='card'><b>Parsed metadata</b><table>{rows or '<tr><td>(none)</td></tr>'}</table></div>"


def _parse_table(df, original_body: str) -> str:
    """The money view: every financial line, raw text vs the number the engine
    actually used. Anything that silently became 0 is the messy-data smell."""
    # Map original raw first-column text so we can flag silent coercions.
    head = "<tr><th>Line item</th><th>Current (used)</th><th>Prior (used)</th></tr>"
    body = []
    for _, r in df.iterrows():
        label = _esc(r.iloc[0])
        cur = r.get("Current", "")
        pri = r.get("Prior", "")
        cur_cls = "num warn" if cur == 0 else "num"
        body.append(f"<tr><td>{label}</td><td class='{cur_cls}'>{_esc(cur)}</td>"
                    f"<td class='num'>{_esc(pri)}</td></tr>")
    note = ("<p class='sub'>Red = parsed to <b>0</b> (value was blank, non-numeric, "
            "or — watch for this — a number containing a comma that split across columns).</p>")
    return (f"<div class='card'><b>Parsed financial rows ({len(df)})</b>"
            f"<table>{head}{''.join(body)}</table>{note}</div>")


def _dict_block(title: str, obj) -> str:
    import json
    def _default(o):
        try:
            return float(o)
        except Exception:
            return str(o)
    try:
        dumped = json.dumps(obj, indent=2, default=_default, ensure_ascii=False)
    except Exception:
        dumped = repr(obj)
    return f"<div class='card'><b>{_esc(title)}</b><pre>{_esc(dumped)}</pre></div>"
