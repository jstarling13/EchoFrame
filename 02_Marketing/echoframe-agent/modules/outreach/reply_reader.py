"""
reply_reader.py — Gmail API integration + LLM-powered reply intent classifier.

Flow:
  1. Poll Gmail for unread emails in the monitored inbox
  2. Match each reply to a lead in the DB by sender email
  3. Classify intent: positive / negative / question / auto_reply
  4. Store the classification + trigger the appropriate response action

Gmail API setup:
  1. Go to console.cloud.google.com
  2. Enable Gmail API
  3. Create OAuth2 credentials (Desktop app)
  4. Download credentials.json → set GMAIL_CREDENTIALS_PATH in .env
  5. First run will open browser for OAuth consent → saves token.json
"""

import base64
import json
import os
import re
from dataclasses import dataclass
from email import message_from_bytes

import anthropic
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import cfg
from modules.outreach.email_sender import add_to_suppression

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# ── CAN-SPAM: stop/unsubscribe keyword detection ──────────────────────────────
# If a reply body contains any of these words (case-insensitive), the sender is
# added to the suppression list immediately, before LLM classification runs.
_STOP_KEYWORDS = re.compile(
    r"\b(stop|unsubscribe|opt.?out|remove me|take me off|do not (email|contact)|"
    r"don.?t (email|contact)|no more emails?)\b",
    re.IGNORECASE,
)

_claude = anthropic.Anthropic(api_key=cfg.anthropic_api_key)


@dataclass
class InboundReply:
    gmail_message_id: str
    from_email: str
    from_name: str
    subject: str
    body: str
    thread_id: str


@dataclass
class ClassifiedReply:
    inbound: InboundReply
    intent: str           # "positive", "negative", "question", "auto_reply"
    confidence: float     # 0–1
    reasoning: str        # LLM's chain-of-thought


# ─── Gmail Auth ───────────────────────────────────────────────────────────────

def _get_gmail_service():
    """Authenticates and returns a Gmail API service object."""
    creds = None

    if os.path.exists(cfg.gmail_token_path):
        creds = Credentials.from_authorized_user_file(cfg.gmail_token_path, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(cfg.gmail_credentials_path):
                raise FileNotFoundError(
                    f"Gmail credentials not found at {cfg.gmail_credentials_path}. "
                    "Follow setup instructions in reply_reader.py docstring."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                cfg.gmail_credentials_path, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(cfg.gmail_token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── Fetch Replies ────────────────────────────────────────────────────────────

def _decode_body(payload: dict) -> str:
    """Recursively extracts plain-text body from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text

    return ""


def fetch_unread_replies(max_results: int = 50) -> list[InboundReply]:
    """
    Fetches unread emails from the monitored Gmail inbox.
    Only returns emails that look like replies (have Re: in subject or are in a thread).
    """
    service = _get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        q="is:unread in:inbox",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    replies = []

    for msg_stub in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_stub["id"],
            format="full",
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        subject = headers.get("subject", "")
        from_raw = headers.get("from", "")
        thread_id = msg.get("threadId", "")

        # Extract email address from "Name <email>" format
        email_match = re.search(r"<([^>]+)>", from_raw)
        from_email = email_match.group(1) if email_match else from_raw
        from_name = from_raw.replace(f"<{from_email}>", "").strip().strip('"')

        body = _decode_body(msg["payload"])

        # Skip auto-generated mail (mailing lists, notifications)
        auto_reply_headers = ["x-autoreply", "x-autorespond", "auto-submitted"]
        if any(h in headers for h in auto_reply_headers):
            # Still return it but flag in body so classifier handles it
            body = f"[AUTO-REPLY DETECTED] {body}"

        replies.append(InboundReply(
            gmail_message_id=msg_stub["id"],
            from_email=from_email.lower(),
            from_name=from_name,
            subject=subject,
            body=body[:2000],  # cap at 2k chars to save tokens
            thread_id=thread_id,
        ))

    return replies


# ─── Intent Classification ────────────────────────────────────────────────────

def classify_intent(reply: InboundReply) -> ClassifiedReply:
    """
    Uses Claude to classify the intent of an inbound reply.
    Returns structured classification with confidence score.

    CAN-SPAM compliance: if the reply body contains stop/unsubscribe keywords,
    the sender is added to the suppression list before any other processing.
    """
    # ── CAN-SPAM: suppress on keyword match (fast path, no LLM cost) ─────────
    if _STOP_KEYWORDS.search(reply.body):
        add_to_suppression(reply.from_email)
        print(f"[CAN-SPAM] Opt-out detected — suppressed {reply.from_email}")
        return ClassifiedReply(
            inbound=reply,
            intent="negative",
            confidence=0.99,
            reasoning="Stop/unsubscribe keyword detected — sender added to suppression list.",
        )

    # Short-circuit obvious auto-replies without burning API tokens
    if "[AUTO-REPLY DETECTED]" in reply.body:
        return ClassifiedReply(
            inbound=reply,
            intent="auto_reply",
            confidence=0.99,
            reasoning="Auto-reply headers detected in email metadata.",
        )

    prompt = f"""Classify the intent of this email reply to a cold outreach sequence.

ORIGINAL OUTREACH CONTEXT: Financial reporting service for small businesses.
Offering a monthly financial clarity report for $150/month.

REPLY FROM: {reply.from_name} ({reply.from_email})
SUBJECT: {reply.subject}
BODY:
{reply.body}

Classify the intent into exactly one of these categories:
- positive: They're interested, want more info, asked about pricing, want to talk, said yes
- negative: Not interested, told us to stop, said no, have a solution already
- question: Asked a specific question about the service, pricing, process, or next steps
- auto_reply: Out-of-office, delivery notification, automated response

Return JSON only:
{{
  "intent": "<category>",
  "confidence": <0.0 to 1.0>,
  "reasoning": "<one sentence explaining your classification>"
}}"""

    response = _claude.messages.create(
        model=cfg.claude_model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback — default to question so we don't ignore it
        parsed = {"intent": "question", "confidence": 0.5, "reasoning": "Parse error — flagged for manual review"}

    return ClassifiedReply(
        inbound=reply,
        intent=parsed.get("intent", "question"),
        confidence=float(parsed.get("confidence", 0.5)),
        reasoning=parsed.get("reasoning", ""),
    )


def fetch_and_classify_all() -> list[ClassifiedReply]:
    """Fetches all unread replies and classifies each one. Main entry point."""
    raw_replies = fetch_unread_replies()
    classified = [classify_intent(r) for r in raw_replies]

    # Summary log
    from collections import Counter
    counts = Counter(c.intent for c in classified)
    print(f"[Reply Reader] Classified {len(classified)} replies: {dict(counts)}")

    return classified
