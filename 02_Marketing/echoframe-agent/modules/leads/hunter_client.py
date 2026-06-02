"""
hunter_client.py — Hunter.io API wrapper for email discovery.

Hunter.io works differently from Apollo:
  - Apollo: search by industry + location → returns contacts directly
  - Hunter: give it a domain → returns emails found at that domain

Our flow:
  1. Google CSE finds local Columbus GA business websites by industry
  2. Hunter.io Domain Search finds the owner email for each domain
  3. Scorer ranks and filters the results

Free plan: 25 searches/month, 25 verifications/month.
Basic plan ($49/mo): 500 searches/month — enough for ~500 leads/month.
"""

import re
import httpx
from dataclasses import dataclass
from config import cfg
from modules.leads.apollo_client import RawLead

HUNTER_BASE = "https://api.hunter.io/v2"

# Titles Hunter commonly returns that indicate a business owner
OWNER_TITLES = {
    "owner", "founder", "co-founder", "co-owner", "president", "ceo",
    "managing partner", "principal", "proprietor", "general manager",
}


@dataclass
class HunterResult:
    domain: str
    company_name: str
    found_emails: list[dict]  # raw Hunter email objects


def domain_search(domain: str, company_name: str = "") -> HunterResult | None:
    """
    Queries Hunter.io for all email addresses found at a given domain.
    Returns None on failure or if no emails found.
    """
    if not cfg.hunter_api_key:
        return None

    # Strip protocol and path — Hunter wants bare domain (e.g. "hvaccolumbus.com")
    domain = re.sub(r"^https?://", "", domain).split("/")[0].strip()
    if not domain:
        return None

    try:
        r = httpx.get(
            f"{HUNTER_BASE}/domain-search",
            params={"domain": domain, "api_key": cfg.hunter_api_key, "limit": 10},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
    except Exception as e:
        print(f"[Hunter] Domain search failed for {domain}: {e}")
        return None

    emails = data.get("emails", [])
    if not emails:
        return None

    return HunterResult(
        domain=domain,
        company_name=company_name or data.get("organization", domain),
        found_emails=emails,
    )


def _extract_best_contact(result: HunterResult, industry: str = "", city: str = "", state: str = "") -> RawLead | None:
    """
    Picks the best contact from a Hunter domain search result.
    Priority: owner/founder title > most common email pattern > first result.
    """
    emails = result.found_emails
    if not emails:
        return None

    # Sort: owner titles first, then by confidence score
    def rank(e):
        title = (e.get("position") or "").lower()
        is_owner = any(t in title for t in OWNER_TITLES)
        confidence = e.get("confidence") or 0
        return (int(is_owner), confidence)

    best = sorted(emails, key=rank, reverse=True)[0]

    email = best.get("value", "")
    if not email:
        return None

    first = best.get("first_name", "")
    last = best.get("last_name", "")
    title = best.get("position", "")
    linkedin = best.get("linkedin", "")
    confidence = best.get("confidence", 0)

    return RawLead(
        first_name=first,
        last_name=last,
        email=email,
        phone="",
        title=title,
        linkedin_url=linkedin or "",
        company_name=result.company_name,
        industry=industry,
        website=result.domain,
        city=city,
        state=state,
        employee_count=0,
        has_verified_email=(confidence >= 80),
        has_phone=False,
        source="hunter",
    )


def enrich_domains_with_hunter(
    domains: list[dict],
) -> list[RawLead]:
    """
    Takes a list of dicts with keys: domain, company_name, industry, city, state.
    Runs each through Hunter and returns a list of RawLeads.

    Each Hunter search costs 1 API credit — caller is responsible for staying
    within the monthly limit.
    """
    leads = []
    for item in domains:
        result = domain_search(item.get("domain", ""), item.get("company_name", ""))
        if not result:
            continue
        lead = _extract_best_contact(
            result,
            industry=item.get("industry", ""),
            city=item.get("city", ""),
            state=item.get("state", ""),
        )
        if lead and lead.email:
            leads.append(lead)
            print(f"[Hunter] Found: {lead.email} @ {lead.company_name} ({lead.title})")

    return leads


def check_credits() -> dict:
    """Returns remaining Hunter.io API credits for the current billing period."""
    try:
        r = httpx.get(
            f"{HUNTER_BASE}/account",
            params={"api_key": cfg.hunter_api_key},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", {})
        requests = data.get("requests", {})
        searches = requests.get("searches", {})
        verifications = requests.get("verifications", {})
        return {
            "searches_used": searches.get("used", 0),
            "searches_available": searches.get("available", 0),
            "verifications_used": verifications.get("used", 0),
            "verifications_available": verifications.get("available", 0),
        }
    except Exception as e:
        print(f"[Hunter] Credit check failed: {e}")
        return {}
