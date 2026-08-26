"""
Tests for the Free First Look intake endpoint (intake.py + the store.py lead
helpers).

Email sends are mocked via unittest.mock.patch on the high-level
intake.emails.send_intake_* functions (the same pattern test_renewals.py uses
for send_upload_link) rather than swapping sys.modules["resend"] at import
time. The whole test suite only ever imports `main` (and therefore `emails`,
which does `import resend` once) a single time; a module-level sys.modules
swap — as test_portal.py does for its own module — only works if that file's
import happens to run first during collection. Patching the specific function
this module calls has no such ordering dependency and can't destabilize
other test files.

The durable store falls back to its in-memory backend (see conftest.py for
the env-var and rate-limit setup shared with the rest of the suite).
"""
from unittest.mock import patch

import pytest

from fastapi.testclient import TestClient

import store
from main import app

client = TestClient(app)

VALID_LEAD = {
    "area": "revenue",
    "product": "callcatch",
    "source": "revenue",
    "business": {"businessName": "Test Plumbing Co", "industry": "Plumbing"},
    "problem": {"leak": "Missed calls", "summary": "We miss a lot of after-hours calls."},
    "contact": {
        "name": "Jamie Test",
        "email": "jamie@example.com",
        "phone": "555-0100",
        "preferred": "Email",
        "operationalConsent": True,
        "marketingConsent": False,
    },
    "fileMetadata": [],
    "createdAt": 1735000000000,
}


def _reset_store():
    if not store.is_configured():
        store._mem.clear()
        store._mem_sets.clear()


@pytest.fixture(autouse=True)
def _clear():
    _reset_store()
    yield
    _reset_store()


@pytest.fixture(autouse=True)
def _mock_emails():
    with patch("intake.emails.send_intake_confirmation") as confirm, \
         patch("intake.emails.send_intake_owner_alert") as owner:
        yield confirm, owner


def _post_lead(lead, files=None):
    import json
    file_parts = [("lead", ("lead.json", json.dumps(lead), "application/json"))]
    if files:
        file_parts += [("files", f) for f in files]
    return client.post("/api/intake", files=file_parts)


def test_successful_submission_no_file(_mock_emails):
    confirm, owner = _mock_emails
    r = _post_lead(VALID_LEAD)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert body["reference"].startswith("EF-")

    # Lead persisted under its own namespace, not the customer/period records.
    saved = store.load_lead(body["reference"])
    assert saved is not None
    assert saved["area"] == "revenue"
    assert saved["contact"]["email"] == "jamie@example.com"
    assert saved["status"] == "new"

    # Both the customer confirmation and the owner alert fire exactly once.
    confirm.assert_called_once()
    owner.assert_called_once()
    assert confirm.call_args.kwargs["to_email"] == "jamie@example.com"
    assert confirm.call_args.kwargs["reference"] == body["reference"]


def test_missing_lead_field_is_validation_error(_mock_emails):
    r = client.post("/api/intake", files={})
    assert r.status_code == 400
    assert r.json()["category"] == "validation"


def test_invalid_area_falls_back_to_validation_not_a_crash(_mock_emails):
    bad = {**VALID_LEAD, "area": "not-a-real-area"}
    r = _post_lead(bad)
    assert r.status_code == 422
    body = r.json()
    assert body["category"] == "validation"
    assert "area" in body["field_errors"]


def test_missing_consent_and_bad_email_are_field_errors(_mock_emails):
    confirm, owner = _mock_emails
    bad = {
        "area": "revenue", "product": "x", "source": "x",
        "business": {}, "problem": {"summary": ""},
        "contact": {"name": "", "email": "not-an-email", "operationalConsent": False},
        "fileMetadata": [], "createdAt": 1,
    }
    r = _post_lead(bad)
    assert r.status_code == 422
    errors = r.json()["field_errors"]
    assert set(errors) == {"name", "email", "operationalConsent", "summary"}
    # No email should go out for a submission that never validated.
    confirm.assert_not_called()
    owner.assert_not_called()


def test_duplicate_submission_returns_existing_reference():
    first = _post_lead(VALID_LEAD)
    assert first.status_code == 200
    first_ref = first.json()["reference"]

    second = _post_lead({**VALID_LEAD, "problem": {**VALID_LEAD["problem"], "summary": "Same person, different words."}})
    assert second.status_code == 409
    body = second.json()
    assert body["category"] == "duplicate_submission"
    assert body["existing_reference"] == first_ref


def test_unsupported_file_extension_rejected(_mock_emails):
    confirm, owner = _mock_emails
    r = _post_lead(VALID_LEAD, files=[("malware.exe", b"not a real exe", "application/octet-stream")])
    assert r.status_code == 422
    assert r.json()["category"] == "unsupported_file"
    confirm.assert_not_called()


def test_oversized_file_rejected(monkeypatch):
    import intake
    monkeypatch.setattr(intake, "MAX_INTAKE_FILE_BYTES", 10)  # 10 bytes, for a fast test
    r = _post_lead(VALID_LEAD, files=[("statement.csv", b"this file is definitely over ten bytes", "text/csv")])
    assert r.status_code == 422
    assert r.json()["category"] == "file_too_large"


def test_too_many_files_rejected():
    files = [(f"file{i}.csv", b"a,b\n1,2", "text/csv") for i in range(4)]
    r = _post_lead(VALID_LEAD, files=files)
    assert r.status_code == 422
    assert r.json()["category"] == "validation"


def test_valid_file_is_attached_to_owner_alert_not_customer_email(_mock_emails):
    confirm, owner = _mock_emails
    r = _post_lead(VALID_LEAD, files=[("bank_export.csv", b"date,amount\n2026-01-01,100", "text/csv")])
    assert r.status_code == 200
    assert owner.call_args.kwargs["attachments"], "owner alert should carry the uploaded file"
    assert "attachments" not in confirm.call_args.kwargs, "customer email must never echo the file back"


def test_lead_can_be_deleted():
    r = _post_lead(VALID_LEAD)
    ref = r.json()["reference"]
    assert store.load_lead(ref) is not None
    store.delete_lead(ref)
    assert store.load_lead(ref) is None
