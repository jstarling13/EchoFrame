"""
google_maps.py — Scrapes Google Maps search results for local businesses.

Uses httpx + BeautifulSoup to pull business names and websites from Google
Maps search results pages. No API key required — just web scraping.

Flow:
  search Google Maps for "HVAC Columbus GA" →
  extract business names + websites →
  feed domains to Hunter.io →
  get owner emails

Note: Google Maps scraping is fragile and may need User-Agent rotation if
volume is high. For 50–100 businesses this works reliably.
"""

import re
import time
import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class LocalBusiness:
    name: str
    domain: str
    industry: str
    city: str
    state: str


def _clean_domain(url: str) -> str:
    """Strips protocol and paths, returns bare domain."""
    url = re.sub(r"^https?://", "", url)
    url = url.split("/")[0].strip()
    # Remove www.
    url = re.sub(r"^www\.", "", url)
    return url


def search_ddg_for_businesses(
    industry: str,
    city: str,
    state: str,
    num_results: int = 15,
) -> list[LocalBusiness]:
    """
    Searches DuckDuckGo HTML for local businesses with websites.
    DDG is scraper-friendly and returns real business URLs without CAPTCHAs.

    Example query: HVAC company Columbus GA
    """
    query = f'{industry} company {city} {state}'
    params = {"q": query, "kl": "us-en"}

    businesses = []
    seen_domains: set[str] = set()

    skip_domains = [
        "google.", "youtube.", "facebook.", "yelp.", "bbb.org",
        "yellowpages", "angi.", "thumbtack", "houzz.", "indeed.",
        "linkedin.", "twitter.", "instagram.", "duckduckgo.",
        "wikipedia.", "homeadvisor.", "porch.com", "bark.com",
        "nextdoor.", "mapquest.", "tripadvisor.",
    ]

    try:
        r = httpx.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=HEADERS,
            timeout=15,
            follow_redirects=True,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # DDG sometimes rate-limits and returns a CAPTCHA/blocked page with no results
        all_results = soup.find_all("div", class_="result")
        if not all_results:
            # Fallback: try grabbing any external links from the page
            all_results = soup.find_all("div", class_=re.compile(r"result"))

        for result_div in all_results:
            # Get the display URL
            url_tag = result_div.find("a", class_="result__url")
            title_tag = result_div.find("a", class_="result__a")

            if not url_tag:
                continue

            raw_url = url_tag.get_text(strip=True)
            if not raw_url:
                # fallback: get href
                raw_url = url_tag.get("href", "")

            if any(s in raw_url for s in skip_domains):
                continue

            domain = _clean_domain(raw_url)
            if not domain or "." not in domain or domain in seen_domains:
                continue

            seen_domains.add(domain)

            name = title_tag.get_text(strip=True) if title_tag else ""
            if not name:
                name = domain.split(".")[0].replace("-", " ").title()

            businesses.append(LocalBusiness(
                name=name,
                domain=domain,
                industry=industry,
                city=city,
                state=state,
            ))

            if len(businesses) >= num_results:
                break

    except Exception as e:
        print(f"[DDG] Search failed for '{industry} {city}': {e}")

    return businesses


# Keep old name as alias so nothing else breaks
def search_google_for_businesses(industry, city, state, num_results=15):
    return search_ddg_for_businesses(industry, city, state, num_results)


def bulk_search_local_businesses(
    industries: list[str] | None = None,
    locations: list[tuple[str, str]] | None = None,
    results_per_query: int = 15,
    delay_seconds: float = 2.0,
) -> list[LocalBusiness]:
    """
    Cross-product search across all industries × locations.
    delay_seconds: pause between requests to avoid rate limiting.

    Returns deduplicated list of LocalBusiness objects with real domains.
    """
    from config import cfg

    industries = industries or cfg.target_industries
    locations = locations or [
        ("Columbus", "GA"),
        ("Phenix City", "AL"),
        ("Auburn", "AL"),
        ("Opelika", "AL"),
    ]

    all_businesses: list[LocalBusiness] = []
    seen_domains: set[str] = set()

    for industry in industries:
        for city, state in locations:
            print(f"[Google] Searching: {industry} in {city}, {state}...")
            results = search_google_for_businesses(
                industry=industry,
                city=city,
                state=state,
                num_results=results_per_query,
            )
            for biz in results:
                if biz.domain not in seen_domains:
                    seen_domains.add(biz.domain)
                    all_businesses.append(biz)

            time.sleep(delay_seconds)

    print(f"[Google] Found {len(all_businesses)} unique business domains.")
    return all_businesses
