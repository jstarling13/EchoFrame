"""
apollo_client.py — Apollo.io API v1 wrapper for lead sourcing.

Apollo is the primary data source. It returns verified emails + phones for
small business owners filtered by industry, location, and company size.

Rate limits: Apollo free tier = 50 exports/month. Paid = 10,000+/month.
"""

import time
import httpx
from dataclasses import dataclass
from config import cfg

APOLLO_BASE = "https://api.apollo.io/v1"


@dataclass
class RawLead:
    first_name: str
    last_name: str
    email: str
    phone: str
    title: str
    linkedin_url: str
    company_name: str
    industry: str
    website: str
    city: str
    state: str
    employee_count: int
    has_verified_email: bool
    has_phone: bool
    source: str = "apollo"


def _apollo_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": cfg.apollo_api_key,
    }


def search_people(
    locations: list[str],
    industries: list[str],
    titles: list[str],
    employee_min: int = 1,
    employee_max: int = 50,
    page: int = 1,
    per_page: int = 100,
) -> list[RawLead]:
    """
    Searches Apollo for people matching the criteria.
    Returns a list of RawLead objects.

    Apollo's people/search endpoint filters by person_titles (role) and
    organization_industry_tag_ids (industry). We map human-readable industry
    names to Apollo's internal tag IDs below.
    """
    payload = {
        "page": page,
        "per_page": per_page,
        "person_titles": titles,
        "person_locations": locations,
        "organization_num_employees_ranges": [f"{employee_min},{employee_max}"],
        # Only pull contacts with at least an email
        "contact_email_status": ["verified", "likely to engage"],
    }

    # Apollo uses free-text industry filtering via q_organization_keyword_tags
    if industries:
        payload["q_organization_keyword_tags"] = industries

    try:
        r = httpx.post(
            f"{APOLLO_BASE}/mixed_people/search",
            json=payload,
            headers=_apollo_headers(),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
    except httpx.HTTPStatusError as e:
        print(f"[Apollo] HTTP error: {e.response.status_code} — {e.response.text[:200]}")
        return []
    except Exception as e:
        print(f"[Apollo] Request failed: {e}")
        return []

    leads = []
    for person in data.get("people", []):
        org = person.get("organization") or {}
        employment = (person.get("employment_history") or [{}])[0]

        email = person.get("email", "")
        if not email:
            continue

        leads.append(RawLead(
            first_name=person.get("first_name", ""),
            last_name=person.get("last_name", ""),
            email=email,
            phone=person.get("sanitized_phone", ""),
            title=person.get("title", ""),
            linkedin_url=person.get("linkedin_url", ""),
            company_name=org.get("name", ""),
            industry=org.get("industry", ""),
            website=org.get("website_url", ""),
            city=person.get("city", ""),
            state=person.get("state", ""),
            employee_count=org.get("num_employees", 0) or 0,
            has_verified_email=person.get("email_status") == "verified",
            has_phone=bool(person.get("sanitized_phone")),
        ))

    return leads


def bulk_source_leads(
    locations: list[str] | None = None,
    industries: list[str] | None = None,
    titles: list[str] | None = None,
    max_leads: int = 200,
) -> list[RawLead]:
    """
    Paginates through Apollo results until max_leads is reached.
    Uses config defaults if params are not provided.
    """
    locations = locations or cfg.target_locations
    industries = industries or cfg.target_industries
    titles = titles or cfg.target_titles

    all_leads: list[RawLead] = []
    page = 1
    per_page = min(100, max_leads)

    while len(all_leads) < max_leads:
        batch = search_people(
            locations=locations,
            industries=industries,
            titles=titles,
            page=page,
            per_page=per_page,
        )
        if not batch:
            break

        all_leads.extend(batch)
        page += 1

        if len(batch) < per_page:
            break  # Apollo returned fewer than requested — we've hit the end

        time.sleep(0.5)  # gentle rate limiting

    return all_leads[:max_leads]
