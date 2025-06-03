import os
import requests
import logging
from typing import List, Dict, Any

logger = logging.getLogger("jewelrybox_ai.websearch")
logger.setLevel(logging.INFO)

# ─── CONFIG & GUARDRAILS ──────────────────────────────────────────────────────

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY is missing from environment variables - web search will be disabled")
    TAVILY_API_KEY = None

# Jewelry-focused allowlist of domains/topics
ALLOWED_DOMAINS = [
    "thediamondfamily.com",
    "jewelryboxai.com",
    "gia.edu",
    "americangemsociety.org",
    "jewelersofamerica.org",
    "diamonds.pro",
    "pricescope.com",
    "bluenile.com",
    "jamesallen.com",
    "brilliantearth.com"
]

DISALLOWED_KEYWORDS = [
    "hack",
    "porn",
    "malware",
    "torrent",
    "crack",
    "pirate",
    "illegal",
    "drugs",
    "violence",
    "weapon"
]

# Jewelry-related keywords that should trigger web search
JEWELRY_KEYWORDS = [
    "diamond",
    "ring",
    "engagement",
    "wedding",
    "jewelry",
    "gemstone",
    "gold",
    "platinum",
    "silver",
    "earrings",
    "necklace",
    "bracelet",
    "watch",
    "appraisal",
    "certification",
    "GIA",
    "clarity",
    "carat",
    "cut",
    "color"
]

def is_query_safe(query: str) -> bool:
    """Check if query is safe and doesn't contain disallowed keywords."""
    lower = query.lower()
    # Block if any disallowed keyword appears
    for bad in DISALLOWED_KEYWORDS:
        if bad in lower:
            return False
    return True

def should_search_web(query: str) -> bool:
    """Determine if query warrants a web search based on jewelry-related keywords."""
    lower = query.lower()
    return any(keyword in lower for keyword in JEWELRY_KEYWORDS)

# ─── WEB SEARCH TOOL ────────────────────────────────────────────────────────────

class WebSearchTool:
    """
    A minimal wrapper around the Tavily Web Search API.
    Ensures queries are safe and limits results to jewelry-relevant domains.
    """

    BASE_URL = "https://api.tavily.com/search"
    HEADERS = {
        "Content-Type": "application/json"
    }

    def __init__(self, allowed_domains: List[str] = None):
        self.allowed_domains = allowed_domains or ALLOWED_DOMAINS
        self.api_key = TAVILY_API_KEY
        
        if not self.api_key:
            raise EnvironmentError("❌ TAVILY_API_KEY is required for WebSearchTool")

    def search(self, query: str, num_results: int = 5) -> str:
        """
        Perform a web search via Tavily; return a formatted string of top results.
        Returns an empty string if query is unsafe or no valid results.
        """

        if not self.api_key:
            return "ℹ️ Web search unavailable - TAVILY_API_KEY not configured."

        if not is_query_safe(query):
            logger.warning(f"Blocked unsafe query: {query}")
            return "⚠️ Your search query appears to be disallowed. Please refine your request."

        # Only search if query is jewelry-related
        if not should_search_web(query):
            logger.info(f"Query not jewelry-related, skipping web search: {query}")
            return ""

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": num_results,
            "include_domains": self.allowed_domains
        }

        try:
            resp = requests.post(self.BASE_URL, json=payload, timeout=8)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Web search timed out for query: {query}")
            return "⏱️ Web search timed out. Using local knowledge base."
        except requests.exceptions.RequestException as e:
            logger.error(f"Web search request failed: {e}")
            return "❌ Web search temporarily unavailable. Using local knowledge base."
        except Exception as e:
            logger.error(f"Unexpected error in web search: {e}")
            return ""

        results = data.get("results", [])
        
        if not results:
            return "ℹ️ No recent web results found. Using local jewelry expertise."

        # Build a simple text block of top results with snippets
        output_lines = ["🌐 **Latest Information:**"]
        for idx, item in enumerate(results[:num_results], start=1):
            title = item.get("title", "No title")
            snippet = item.get("content", "").strip().replace("\n", " ")
            url = item.get("url", "")
            
            # Truncate snippet if too long
            if len(snippet) > 150:
                snippet = snippet[:150] + "..."
            
            output_lines.append(f"{idx}. **{title}**")
            if snippet:
                output_lines.append(f"   {snippet}")
            output_lines.append(f"   Source: {url}")
            output_lines.append("")

        return "\n".join(output_lines) 