"""
google_search.py — Google Custom Search API for supplemental lead discovery.

Used when Apollo doesn't have coverage for hyper-local Columbus GA businesses.
Searches for business websites, then extracts owner contact info.

Setup: Create a Custom Search Engine at programmablesearchengine.google.com
       Enable it to search the whole web. Get API key from console.cloud.google.com.
"""

import re
import httpx
from dataclasses import dataclass, field

from config import cfg

GOOGLE_CSE_BASE = "https://www.googleapis.com/customsearch/v1"


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    # Extracted during enrichment pass
    business_name: str = ""
    industry_guess: str = ""
    contact_page_url: str = ""
    found_email: str = ""
    found_phone: str = ""


def search_local_businesses(
    industry: str,
    location: str,
    num_results: int = 10,
) -> list[SearchResult]:
    """
    Searches Google for local businesses in a specific industry + location.
    Returns raw search results to be enriched downstream.
    """
    if not cfg.google_cse_api_key or not cfg.google_cse_cx:
        print("[Google CSE] API key or CX not configured — skipping.")
        return []

    query = f'"{industry}" business owner "{location}" contact'

    params = {
        "key": cfg.google_cse_api_key,
        "cx": cfg.google_cse_cx,
        "q": query,
        "num": min(num_results, 10),  # Google caps at 10 per request
    }

    try:
        r = httpx.get(GOOGLE_CSE_BASE, params=params, timeout=15)
        r.raise_for_status()
        items = r.json().get("items", [])
    except Exception as e:
        print(f"[Google CSE] Search failed: {e}")
        return []

    results = []
    for item in items:
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
            industry_guess=industry,
        ))

    return results


def _extract_emails(text: str) -> list[str]:
    """Pulls email addresses from raw HTML/text."""
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    found = re.findall(pattern, text)
    # Filter out obvious non-person emails
    skip = {"noreply", "info@", "contact@", "support@", "hello@", "admin@"}
    return [e for e in found if not any(s in e.lower() for s in skip)]


def _extract_phones(text: str) -> list[str]:
    """Pulls US phone numbers from raw text."""
    pattern = r"(\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})"
    return re.findall(pattern, text)


def enrich_from_website(result: SearchResult) -> SearchResult:
    """
    Fetches the business website and attempts to extract owner contact info.
    Modifies and returns the SearchResult in place.
    """
    try:
        r = httpx.get(result.url, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"})
        text = r.text

        emails = _extract_emails(text)
        if emails:
            result.found_email = emails[0]

        phones = _extract_phones(text)
        if phones:
            result.found_phone = phones[0]

        # Try the /contact page if nothing found
        if not result.found_email:
            contact_url = result.url.rstrip("/") + "/contact"
            try:
                rc = httpx.get(contact_url, timeout=8, follow_redirects=True,
                               headers={"User-Agent": "Mozilla/5.0"})
                extra_emails = _extract_emails(rc.text)
                if extra_emails:
                    result.found_email = extra_emails[0]
                    result.contact_page_url = contact_url
            except Exception:
                pass

    except Exception as e:
        print(f"[Google CSE] Enrichment failed for {result.url}: {e}")

    return result


def source_local_leads_via_google(
    industries: list[str] | None = None,
    locations: list[str] | None = None,
    results_per_query: int = 10,
) -> list[SearchResult]:
    """
    Cross-product search across all industries × locations.
    Enriches each result with contact info.
    Returns only results that have at least an email.
    """
    industries = industries or cfg.target_industries
    locations = locations or cfg.target_locations

    all_results = []
    for industry in industries:
        for location in locations:
            batch = search_local_businesses(industry, location, results_per_query)
            for result in batch:
                enriched = enrich_from_website(result)
                if enriched.found_email:
                    all_results.append(enriched)

    return all_results
