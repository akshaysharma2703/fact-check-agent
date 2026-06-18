import logging
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def perform_search(query: str, max_results: int = 3) -> List[Dict]:
    """
    Performs a DuckDuckGo search for the given query.
    
    Args:
        query: The search term string.
        max_results: The maximum number of search results to return.
        
    Returns:
        A list of dicts: [{'title': ..., 'url': ..., 'snippet': ...}]
    """
    search_results = []
    try:
        logger.info(f"Performing search query: '{query}'")
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            if results:
                for r in results:
                    search_results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
        logger.info(f"Retrieved {len(search_results)} results for query: '{query}'")
    except Exception as e:
        logger.error(f"DuckDuckGo search error for query '{query}': {str(e)}")
        # Return empty list in case of rate limits or connectivity issues
        
    return search_results

def scrape_url(url: str, timeout: int = 6) -> str:
    """
    Scrapes the text content of a given URL.
    
    Args:
        url: The website URL to scrape.
        timeout: Request timeout in seconds.
        
    Returns:
        A clean string of text content from the page, or an empty string if it fails.
    """
    if not url.startswith("http"):
        return ""
    try:
        logger.info(f"Scraping URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Decompose script, style, nav, and footer elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
                
            text = soup.get_text()
            # Clean up spacing
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)
            
            # Keep up to first 12,000 characters to prevent prompt bloating
            return clean_text[:12000]
        else:
            logger.warning(f"Non-200 status code ({response.status_code}) for URL: {url}")
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {str(e)}")
        
    return ""

def search_and_retrieve_context(query: str, max_results: int = 2) -> List[Dict]:
    """
    Combines search and scraping to return search results along with full-text scraped contents.
    
    Args:
        query: The search term query.
        max_results: The maximum number of results to fetch and scrape.
        
    Returns:
        A list of dicts with keys: title, url, snippet, content.
    """
    results = perform_search(query, max_results=max_results)
    detailed_results = []
    
    for r in results:
        url = r["url"]
        content = scrape_url(url)
        # If scraping failed, use the search result snippet as fallback content
        if not content:
            content = r["snippet"]
        
        detailed_results.append({
            "title": r["title"],
            "url": url,
            "snippet": r["snippet"],
            "content": content
        })
        
    return detailed_results
