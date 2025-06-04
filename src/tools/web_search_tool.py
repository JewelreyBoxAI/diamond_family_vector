import os
import requests
import logging
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

logger = logging.getLogger("diamond_family_ai.websearch")
logger.setLevel(logging.INFO)

# ─── CONFIG & GUARDRAILS ──────────────────────────────────────────────────────

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logger.warning("TAVILY_API_KEY is missing from environment variables - web search will be disabled")
    TAVILY_API_KEY = None

# Jewelry industry domain whitelist for security
JEWELRY_DOMAINS = {
    "gia.edu",
    "americangemsociety.org", 
    "agta.org",
    "jckonline.com",
    "thediamondfamily.com",
    "rjcresponsibility.org",
    "kimberleyprocess.com",
    "gemguide.com",
    "rapaport.com",
    "professional-jeweller.com",
    "diamondfamilyai.com",  # Our own domain
    "nationalyewelernetwork.com",
    "jewelers.org",
    "polygon.net"
}

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

def verify_url(url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Verify if a URL is accessible and return status information.
    Returns dict with 'accessible', 'status_code', and 'error' keys.
    """
    try:
        # Parse URL to ensure it's valid
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return {"accessible": False, "status_code": None, "error": "Invalid URL format"}
        
        # Make HEAD request to check accessibility without downloading content
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        # Consider 2xx and 3xx status codes as accessible
        accessible = 200 <= response.status_code < 400
        
        return {
            "accessible": accessible,
            "status_code": response.status_code,
            "error": None if accessible else f"HTTP {response.status_code}"
        }
        
    except requests.exceptions.Timeout:
        return {"accessible": False, "status_code": None, "error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return {"accessible": False, "status_code": None, "error": "Connection failed"}
    except requests.exceptions.RequestException as e:
        return {"accessible": False, "status_code": None, "error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"accessible": False, "status_code": None, "error": f"Unexpected error: {str(e)}"}

def extract_urls_from_text(text: str) -> List[str]:
    """Extract all URLs from text using regex."""
    url_pattern = r'https?://[^\s<>"]+[^\s<>".,;!?]'
    return re.findall(url_pattern, text)

def verify_urls_in_response(response_text: str) -> str:
    """
    Verify all URLs in a response text and handle them naturally.
    Returns modified response with natural URL handling.
    """
    urls = extract_urls_from_text(response_text)
    
    if not urls:
        return response_text
    
    logger.info(f"🔍 Verifying {len(urls)} URLs in response...")
    modified_response = response_text
    
    for url in urls:
        verification = verify_url(url)
        
        if verification["accessible"]:
            logger.info(f"✅ URL verified: {url}")
            # Keep URLs as-is when they work - no need to add indicators
        else:
            logger.warning(f"❌ URL verification failed: {url} - {verification['error']}")
            # For inaccessible URLs, just keep them natural - don't add AI warnings
            # The AI should handle this contextually in future responses
    
    return modified_response

# ─── WEB SEARCH TOOL ────────────────────────────────────────────────────────────

class WebSearchTool:
    """
    A minimal wrapper around the Tavily Web Search API.
    Ensures queries are safe and limits results to jewelry-relevant domains.
    Includes URL verification capabilities.
    """

    BASE_URL = "https://api.tavily.com/search"
    HEADERS = {
        "Content-Type": "application/json"
    }

    def __init__(self, allowed_domains: List[str] = None, verify_urls: bool = True):
        self.allowed_domains = allowed_domains or JEWELRY_DOMAINS
        self.api_key = TAVILY_API_KEY
        self.verify_urls = verify_urls
        
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
            
            # Verify URL if verification is enabled
            if self.verify_urls and url:
                verification = verify_url(url)
                if verification["accessible"]:
                    url_display = f"{url} ✅"
                else:
                    url_display = f"{url} ⚠️"
                    logger.warning(f"Search result URL verification failed: {url} - {verification['error']}")
            else:
                url_display = url
            
            output_lines.append(f"{idx}. **{title}**")
            if snippet:
                output_lines.append(f"   {snippet}")
            output_lines.append(f"   Source: {url_display}")
            output_lines.append("")

        return "\n".join(output_lines) 