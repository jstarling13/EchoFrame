"""
config.py — Central configuration for the EchoFrame autonomous marketing agent.

All secrets are loaded from .env. Never hardcode keys here.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # ── LLM ──────────────────────────────────────────────────────────────────
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    claude_model: str = "claude-sonnet-4-6"

    # ── Lead Generation ───────────────────────────────────────────────────────
    apollo_api_key: str = field(default_factory=lambda: os.getenv("APOLLO_API_KEY", ""))
    hunter_api_key: str = field(default_factory=lambda: os.getenv("HUNTER_API_KEY", ""))
    google_cse_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_CSE_API_KEY", ""))
    google_cse_cx: str = field(default_factory=lambda: os.getenv("GOOGLE_CSE_CX", ""))  # Custom Search Engine ID

    # ── Email / Outreach ──────────────────────────────────────────────────────
    resend_api_key: str = field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    from_email: str = "jacobstarling4313@gmail.com"
    from_name: str = "Jacob Starling | EchoFrame"

    # ── CAN-SPAM required fields ──────────────────────────────────────────────
    # Every commercial email must include a valid physical postal address and a
    # clear opt-out mechanism (15 U.S.C. § 7704).
    # TODO: Replace the placeholder below with your real mailing address
    #       (a registered business address or USPS PO Box — never leave it blank).
    physical_mailing_address: str = "TODO: Your mailing address here (e.g. PO Box 1234, Columbus GA 31901)"
    # TODO: Replace with either:
    #   - A mailto: address that logs opt-outs  (e.g. "unsubscribe@yourdomain.com")
    #   - A full https:// URL to a one-click unsubscribe page
    unsubscribe_url_or_email: str = "TODO: unsubscribe@yourdomain.com"

    # ── Gmail Reply Monitoring ────────────────────────────────────────────────
    # OAuth2 credentials JSON path for Gmail API
    gmail_credentials_path: str = field(
        default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_PATH", "data/gmail_credentials.json")
    )
    gmail_token_path: str = "data/gmail_token.json"
    gmail_monitored_address: str = field(
        default_factory=lambda: os.getenv("GMAIL_MONITORED_ADDRESS", "jacobstarling4313@gmail.com")
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/echoframe_agent.db")
    )

    # ── Lead Targeting ────────────────────────────────────────────────────────
    # Primary markets: Columbus GA + surrounding (home services first, then restaurant/salon)
    target_locations: list = field(default_factory=lambda: [
        "Columbus, GA",
        "Phenix City, AL",
        "Auburn, AL",
        "Opelika, AL",
    ])
    target_industries: list = field(default_factory=lambda: [
        "HVAC",
        "Plumbing",
        "Electrical",
        "Roofing",
        "Landscaping",
        "Restaurant",
        "Salon",
        "Auto Repair",
    ])
    target_employee_range: tuple = (1, 50)
    target_titles: list = field(default_factory=lambda: [
        "Owner", "Founder", "CEO", "President", "General Manager", "Co-Owner"
    ])

    # ── Outreach Sequencing ───────────────────────────────────────────────────
    # Days between touches in the 5-email sequence
    sequence_delays_days: list = field(default_factory=lambda: [0, 3, 7, 14, 21])
    # Send window: Tue–Thu, 7–9am local
    send_days: list = field(default_factory=lambda: [1, 2, 3])  # Mon=0, so Tue=1, Wed=2, Thu=3
    send_hour_start: int = 7
    send_hour_end: int = 9

    # ── Agent Behavior ────────────────────────────────────────────────────────
    leads_per_run: int = 50        # How many new leads to source per agent cycle
    max_concurrent_sequences: int = 200  # Max active outreach threads at once
    reply_check_interval_minutes: int = 60

    # ── A/B Testing ───────────────────────────────────────────────────────────
    # Minimum replies before a template variant is statistically eligible for replacement
    min_replies_for_optimization: int = 20
    # If reply rate drops below this threshold, trigger rewrite
    reply_rate_floor: float = 0.04  # 4%


# Singleton
cfg = Config()
