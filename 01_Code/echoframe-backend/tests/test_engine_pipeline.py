"""
EchoFrame engine pipeline tests
─────────────────────────────────────────────────────────────────────────────
Covers the report persistence + delivery path and the full end-to-end pipeline
with ALL external services mocked (no Anthropic, no Resend, no network).

These tests specifically guard the reconstructed _save_report /
_send_report_email functions (lost to a file truncation, restored 2026-06-02)
so the regression cannot silently recur: if either is missing or its contract
changes, these fail.

Run:  pytest tests/test_engine_pipeline.py -v
"""

import base64
from unittest.mock import patch, MagicMock

from products.clarity import clarity_engine as engine


# ── _report_slug / _save_report naming ────────────────────────────────────────

class TestReportSlug:
    def test_business_name_slugified(self):
        assert engine._report_slug("Reliable Heating & Air") == "reliable_heating_air"

    def test_accented_and_symbols_collapse(self):
        # 'Lumière Salon & Spa' → 'lumi_re_salon_spa' (matches prior on-disk reports)
        assert engine._report_slug("Lumière Salon & Spa") == "lumi_re_salon_spa"

    def test_empty_falls_back_to_report(self):
        assert engine._report_slug("") == "report"
        assert engine._report_slug("   ") == "report"


class TestSaveReport:
    def test_writes_docx_with_expected_filename(self, tmp_path):
        original = engine.REPORTS_DIR
        engine.REPORTS_DIR = tmp_path
        try:
            path = engine._save_report(
                "owner@example.com", b"PK\x03\x04 fake docx bytes",
                {"Business Name": "Fork & Fire Kitchen"},
            )
            from pathlib import Path
            p = Path(path)
            assert p.exists()
            assert p.name.startswith("EchoFrame_fork_fire_kitchen_")
            assert p.name.endswith(".docx")
            assert p.read_bytes() == b"PK\x03\x04 fake docx bytes"
        finally:
            engine.REPORTS_DIR = original


# ── _send_report_email (Resend mocked — never hits the network) ────────────────

class TestSendReportEmail:
    def test_send_builds_base64_attachment_and_calls_resend(self):
        attachment = b"\x50\x4b\x03\x04 real-looking docx"
        with patch("products.clarity.clarity_engine.resend.Emails.send") as mock_send:
            engine._send_report_email(
                "client@example.com", "Shane", attachment,
                {"Business Name": "Reliable Heating & Air", "Month": "May 2026"},
            )
        assert mock_send.called, "Resend send must be invoked"
        params = mock_send.call_args[0][0]
        assert params["to"] == ["client@example.com"]
        assert "May 2026" in params["subject"]
        assert params["attachments"], "an attachment must be present"
        decoded = base64.b64decode(params["attachments"][0]["content"])
        assert decoded == attachment, "attachment must round-trip through base64"

    def test_send_failure_propagates(self):
        with patch("products.clarity.clarity_engine.resend.Emails.send", side_effect=RuntimeError("resend down")):
            try:
                engine._send_report_email(
                    "c@example.com", "X", b"x", {"Business Name": "Y", "Month": "May 2026"}
                )
                assert False, "expected the send failure to propagate"
            except RuntimeError:
                pass


# ── Full pipeline end-to-end (narrative + email mocked) ────────────────────────

_CANNED_PROSE = {
    "executive_summary": "$52,000 in revenue, up 18.2%, with net income of $12,636 (24.3% margin).",
    "revenue_analysis": "Revenue reflects peak spring demand.",
    "revenue_bullets_insight": ["a", "b", "c"],
    "revenue_bullets_next": ["x", "y"],
    "leak_1_analysis": "Labor is $520 above benchmark. Review payroll.",
    "leak_2_analysis": "Equipment is elevated by one-time purchases.",
    "leak_3_analysis": "Vehicle cost slightly high due to a repair.",
    "leak_4_analysis": "Parts within band.",
    "leak_5_analysis": "Misc unremarkable.",
    "cash_flow_analysis": "Positive cash month.",
    "cash_flow_bullets": ["a", "b", "c"],
    "projection_base_case": "Margins normalize.",
    "projection_quick_wins": "Scheduling holds margin.",
    "projection_full_plan": "Full plan supports margin and pipeline.",
    "one_thing_why": "Labor is the largest controllable cost.",
    "one_thing_risk": "Evaluate response times before trimming shifts.",
    "one_thing_steps": ["Pull payroll.", "Match hours.", "Draft schedule.", "Confirm coverage."],
    "one_thing_impact": "Recovers about $520/mo.",
    "next_step_this_week": "Pull the payroll register.",
    "next_step_this_month": "Build a demand-aligned schedule.",
    "next_step_30_days": "Restore a marketing floor.",
    "next_step_60_days": "Reconcile equipment as capital.",
    "next_step_90_days": "Review trailing labor percent.",
    "closing_sentence": "Next month tracks labor %, utility spend, and marketing allocation.",
}

_SAMPLE_CSV = (
    "_Business Name,Reliable Heating & Air,\n"
    "_Owner Name,Shane,\n"
    "_Industry,HVAC,\n"
    "_Location,Columbus GA,\n"
    "_Month,May 2026,\n"
    "Revenue,52000,44000\n"
    "Labor Cost,18720,14080\n"
    "Parts & Materials,9360,8800\n"
    "Marketing,780,880\n"
    "Utilities,624,528\n"
    "Misc,1040,880\n"
)


class TestFullPipelineMocked:
    def test_generate_clarity_report_end_to_end(self, tmp_path):
        orig_up, orig_rep = engine.UPLOADS_DIR, engine.REPORTS_DIR
        engine.UPLOADS_DIR = tmp_path
        engine.REPORTS_DIR = tmp_path
        try:
            safe = engine._safe_email("e2e@example.com")
            (tmp_path / f"{safe}.csv").write_text(_SAMPLE_CSV, encoding="utf-8")

            with patch("products.clarity.clarity_engine._generate_narrative", return_value=dict(_CANNED_PROSE)), \
                 patch("products.clarity.clarity_engine.resend.Emails.send") as mock_send:
                path = engine.generate_clarity_report(
                    "e2e@example.com", "Shane", "HVAC", "Columbus GA"
                )

            from pathlib import Path
            assert path and Path(path).exists()
            assert Path(path).stat().st_size > 10_000, "a real .docx should be produced"
            assert mock_send.called, "email step should run (mocked)"
        finally:
            engine.UPLOADS_DIR = orig_up
            engine.REPORTS_DIR = orig_rep

    def test_zero_revenue_raises_valueerror(self, tmp_path):
        orig_up = engine.UPLOADS_DIR
        engine.UPLOADS_DIR = tmp_path
        try:
            safe = engine._safe_email("zero@example.com")
            (tmp_path / f"{safe}.csv").write_text(
                "_Business Name,Zero Co,\nRevenue,0,0\nLabor Cost,100,100\n", encoding="utf-8"
            )
            with patch("products.clarity.clarity_engine._generate_narrative", return_value=dict(_CANNED_PROSE)), \
                 patch("products.clarity.clarity_engine.resend.Emails.send"):
                try:
                    engine.generate_clarity_report("zero@example.com", "Z", "HVAC", "GA")
                    assert False, "zero revenue must raise"
                except ValueError:
                    pass
        finally:
            engine.UPLOADS_DIR = orig_up
