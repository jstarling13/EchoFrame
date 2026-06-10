"""
knowledge_base.py — EchoFrame self-training module.

Builds a persistent ChromaDB vector store from:
  1. The hardcoded EchoFrame business profile
  2. Any scraped web content (landing page, sample reports)
  3. Existing outreach templates and pitch scripts

The copywriting engine queries this store to ground every email it writes
in EchoFrame's actual tone, data, and value propositions.
"""

import hashlib
import httpx
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils import embedding_functions
from config import cfg

# Persistent ChromaDB stored on disk so it survives between runs
_chroma_client = chromadb.PersistentClient(path="data/knowledge_base")
_embed_fn = embedding_functions.DefaultEmbeddingFunction()

COLLECTION_NAME = "echoframe_kb"


def _get_collection():
    return _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_embed_fn,
    )


# ─── Static Business Profile ─────────────────────────────────────────────────
# Everything the agent needs to know about EchoFrame, in natural language.
# Structured as discrete facts so vector retrieval is precise.

ECHOFRAME_FACTS = [
    # Core Value Proposition
    "EchoFrame delivers CFO-level financial intelligence to small business owners "
    "who can't afford a CFO. The finished product is a polished Word document report "
    "they receive by email — no software to learn, no dashboard to log into.",

    "EchoFrame's single most powerful claim: clients discover a median of $1,200+ "
    "in cost leaks per report. One discovery pays for 12 months of the subscription.",

    "The report takes a simple CSV upload (income and expenses) and produces: "
    "a business health score, revenue trend analysis, top 5 expense leaks ranked by "
    "dollar impact, 90-day cash flow projection, and one prioritized action item.",

    "EchoFrame uses industry-specific benchmarks — a restaurant's food cost is "
    "benchmarked differently than an HVAC company's labor cost. The analysis is "
    "relevant, not generic.",

    # Pricing
    "EchoFrame pricing: $150/month for the Monthly Clarity Report subscription. "
    "$499 one-time for a Business Audit. $299 one-time for a Competitor Intelligence report.",

    "The $150/month report is the anchor product. It's positioned as cheaper than "
    "one hour of a CPA's time but delivers ongoing monthly insight.",

    # Target Customer
    "Primary target: Small business owners in Columbus GA and surrounding area "
    "(Phenix City AL, Auburn AL). Owner-operators of HVAC, plumbing, electrical, "
    "roofing, landscaping companies — 1 to 50 employees.",

    "Secondary target: Restaurant and salon owners in the same geography. "
    "These owners are emotionally attached to their businesses, work long hours, "
    "and feel like money disappears despite being busy.",

    "The ideal customer is NOT an accountant. They are the person who built the "
    "business with their hands and now doesn't have time to understand the numbers. "
    "They use QuickBooks but don't look at it. They have a CPA who files taxes but "
    "never calls them to explain what's happening.",

    # Competitive Differentiation
    "EchoFrame vs CPA: A CPA is a historian — they explain what happened last year "
    "for tax purposes. EchoFrame is a co-pilot — it tells you what's happening now "
    "and what to do about it next quarter.",

    "EchoFrame vs QuickBooks: QuickBooks shows you everything. EchoFrame tells you "
    "what matters. The difference is signal vs noise.",

    "EchoFrame vs generic AI (ChatGPT): Generic AI gives you a calculator. EchoFrame "
    "gives you industry-calibrated analysis — an HVAC benchmark database built into "
    "the engine that ChatGPT doesn't have.",

    # Pain Points That Drive Conversions
    "The #1 emotional pain for HVAC owners: the 'misc' expense bucket. It grows "
    "every month and nobody knows what's in it. EchoFrame breaks it open.",

    "The #1 emotional pain for restaurant owners: food cost percentage creep. "
    "They know their margins are thin but can't see where the leaks are week to week.",

    "The universal pain: 'I'm busy, the business is making money, but I never "
    "have any cash.' EchoFrame diagnoses the gap between revenue and cash position.",

    # Founder Credibility
    "EchoFrame is run by Jacob Starling: Master of Finance (Emory University), "
    "Investment Analyst at Blue Eagle Capital, Navy OCS candidate (August 2026). "
    "This is not a SaaS startup — it's a financial professional offering a service.",

    "Jacob's background means the analysis isn't just AI output — it's built on "
    "the same benchmarking frameworks used by institutional investors to evaluate "
    "small business portfolios.",

    # Social Proof (from sample reports / testimonials)
    "Sample result from an HVAC client: identified $2,800 in miscellaneous expense "
    "leaks and $42,000 in slow-paying receivables. Both were invisible before the report.",

    "The report format is designed to be shown to employees, lenders, or investors. "
    "Owners say it makes them look like they have a real finance team.",

    # Objection Handling
    "Most common objection: 'I already have a bookkeeper / CPA.' "
    "Response: Your bookkeeper records. Your CPA files. Neither one calls you on a "
    "Tuesday to say your payroll just crossed 38% of revenue and your industry benchmark "
    "is 32%. That's the gap EchoFrame fills.",

    "Second most common objection: 'I don't have time for this.' "
    "Response: You upload one CSV. You get a report by email. It takes you 5 minutes "
    "to read. If it finds $500 in monthly savings, that's $6,000 a year for 5 minutes.",

    # Tone & Voice Rules
    "EchoFrame's tone: Direct, specific, no jargon. Never say 'leverage,' 'synergies,' "
    "'game-changing,' or 'robust.' Use numbers whenever possible. Sound like a smart "
    "friend who happens to be a CFO, not a vendor selling software.",

    "Email tone rule: Short paragraphs. No more than 3 sentences per paragraph. "
    "Subject lines under 50 characters. No exclamation points. No emojis in B2B email.",
]

# ─── Web Scraping ─────────────────────────────────────────────────────────────

def _scrape_url(url: str) -> str:
    """Fetches a URL and returns clean text. Returns empty string on failure."""
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return " ".join(soup.get_text(separator=" ").split())
    except Exception:
        return ""


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Splits long text into overlapping chunks for better vector retrieval."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


# ─── Public API ───────────────────────────────────────────────────────────────

def build_knowledge_base(extra_urls: list[str] | None = None) -> None:
    """
    (Re)builds the ChromaDB collection from static facts + optional web scraping.
    Safe to call on every agent startup — uses content hashes to skip unchanged docs.
    """
    col = _get_collection()
    docs, ids, metas = [], [], []

    # Static business facts
    for i, fact in enumerate(ECHOFRAME_FACTS):
        doc_id = f"static_{hashlib.md5(fact.encode()).hexdigest()[:12]}"
        docs.append(fact)
        ids.append(doc_id)
        metas.append({"source": "static", "type": "business_fact"})

    # Scrape any additional URLs (landing page, etc.)
    for url in (extra_urls or []):
        raw = _scrape_url(url)
        if not raw:
            continue
        for j, chunk in enumerate(_chunk_text(raw)):
            doc_id = f"web_{hashlib.md5((url + str(j)).encode()).hexdigest()[:12]}"
            docs.append(chunk)
            ids.append(doc_id)
            metas.append({"source": url, "type": "scraped_web"})

    if docs:
        # upsert is idempotent — safe to re-run
        col.upsert(documents=docs, ids=ids, metadatas=metas)

    print(f"[KB] Knowledge base contains {col.count()} documents.")


def query_kb(query: str, n_results: int = 5) -> list[str]:
    """Returns the most relevant KB passages for a given query string."""
    col = _get_collection()
    if col.count() == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n_results, col.count()))
    return results["documents"][0] if results["documents"] else []


def get_value_prop_for_industry(industry: str) -> list[str]:
    """Fetches KB passages most relevant to a specific industry's pain points."""
    return query_kb(
        f"EchoFrame value proposition pain points {industry} small business owner",
        n_results=6,
    )
