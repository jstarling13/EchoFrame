"""
Shared pytest configuration for EchoFrame security tests.
Sets test environment variables before any app module is imported.
"""
import os
import pytest

# Ensure test-safe placeholder values are present before app import.
# All four are required at startup (see main.py _REQUIRED_ENV_VARS).
# Use explicit assignment so empty-string system env vars are replaced with safe placeholders.
#
# PUBLIC_BASE_URL and SIGNING_SECRET are read into module-level constants by
# main.py at import time (not read live), and main/emails/portal/intake are
# each imported exactly once per test session — whichever test file happens
# to trigger that first import "locks in" these two for every other file.
# test_portal.py and test_renewals.py used to each set their own via
# os.environ.setdefault() as a defensive guard against exactly this, but that
# only works if one of THEM is the file that runs first; any other test file
# that imports main first (e.g. one added later, alphabetically earlier)
# silently caches empty/wrong values for the rest of the session. Setting
# them here removes the ordering dependency entirely — both existing
# setdefault() calls already use these same values, so this is a no-op for
# them and simply extends the guarantee to every test file.
_CONFTEST_DEFAULTS = {
    "STRIPE_SECRET_KEY":               "sk_test_placeholder",
    "STRIPE_WEBHOOK_SECRET":           "whsec_test_placeholder",
    "ANTHROPIC_API_KEY":               "sk-ant-test-placeholder",
    "RESEND_API_KEY":                  "re_test_placeholder",
    "CLIENT_URL":                      "http://localhost:3000",
    "PRICE_ID_MONTHLY_CLARITY_REPORT": "price_test_monthly",
    "PRICE_ID_BUSINESS_AUDIT":         "price_test_audit",
    "PRICE_ID_COMPETITOR_REPORT":      "price_test_competitor",
    "PUBLIC_BASE_URL":                 "https://app.echoframe.net",
    "SIGNING_SECRET":                  "conftest-shared-test-signing-secret",
}
for _k, _v in _CONFTEST_DEFAULTS.items():
    if not os.environ.get(_k):  # covers both absent AND empty-string values
        os.environ[_k] = _v

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(autouse=True)
def disable_rate_limits():
    """Disable rate limiting during tests.

    Without this, tests sharing the same IP (127.0.0.1) trip the limiter
    after 5 sequential /api/upload calls and return 429 instead of the
    status code the test is actually asserting.

    Strategy: set limiter._enabled = False on the app's limiter instance.
    This is the cleanest approach — slowapi's _check_request_limit returns
    immediately when _enabled is False, so request.state.view_rate_limit is
    never read and no KeyError is raised.
    """
    from main import limiter as _limiter
    original_enabled = _limiter.enabled
    _limiter.enabled = False
    yield
    _limiter.enabled = original_enabled
