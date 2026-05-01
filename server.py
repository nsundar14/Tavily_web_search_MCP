"""
Web Search MCP Server - SSE Transport
Search the web using DuckDuckGo (no API key) + Optional Tavily integration
Demonstrates environment variable handling in production
"""

from fastmcp import FastMCP
import os
import requests
from typing import Optional, Dict, Any

# Optional: Load .env file for local development (not used in production)
try:
    from dotenv import load_dotenv
    load_dotenv()  # Only loads if .env file exists (local dev)
except ImportError:
    pass  # python-dotenv not installed (production - no problem!)

# Initialize FastMCP server
mcp = FastMCP("Web Search MCP")

# Get API keys from environment
# In development: Reads from .env file (if load_dotenv() ran)
# In production: Reads from Kubernetes-injected env vars (no .env file needed!)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")  # Optional alternative
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "5"))
TIMEOUT = int(os.getenv("TIMEOUT", "10"))

@mcp.tool()
def search_web(query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
    """
    Search the web for information.
    
    Args:
        query: Search query
        max_results: Maximum number of results (default from env)
    
    Returns:
        Search results with titles, URLs, and snippets
    """
    max_res = max_results or MAX_RESULTS
    
    # Use Tavily if API key is configured
    if TAVILY_API_KEY:
        return _search_tavily(query, max_res)
    elif SERPER_API_KEY:
        return _search_serper(query, max_res)
    else:
        return _search_duckduckgo(query, max_res)

@mcp.tool()
def search_news(query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
    """
    Search for recent news articles.
    
    Args:
        query: News search query
        max_results: Maximum number of results
    
    Returns:
        Recent news articles matching the query
    """
    max_res = max_results or MAX_RESULTS
    
    if TAVILY_API_KEY:
        return _search_tavily(query, max_res, search_type="news")
    else:
        return _search_duckduckgo(f"{query} news", max_res)

@mcp.tool()
def get_search_config() -> Dict[str, Any]:
    """
    Get current search configuration.
    Shows which API keys are configured.
    
    Returns:
        Configuration status
    """
    return {
        "provider": "tavily" if TAVILY_API_KEY else "serper" if SERPER_API_KEY else "duckduckgo",
        "tavily_configured": bool(TAVILY_API_KEY),
        "serper_configured": bool(SERPER_API_KEY),
        "max_results_default": MAX_RESULTS,
        "timeout": TIMEOUT,
        "note": "DuckDuckGo is used as fallback (no API key needed)"
    }

def _search_tavily(query: str, max_results: int, search_type: str = "search") -> Dict[str, Any]:
    """Search using Tavily API"""
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": True,
            "include_domains": [],
            "exclude_domains": []
        }
        
        if search_type == "news":
            payload["topic"] = "news"
        
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("results", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "score": item.get("score", 0)
            })
        
        return {
            "provider": "tavily",
            "query": query,
            "results_count": len(results),
            "answer": data.get("answer"),
            "results": results
        }
    
    except Exception as e:
        return {
            "error": f"Tavily search failed: {str(e)}",
            "fallback": "Try using DuckDuckGo (no API key needed)"
        }

def _search_serper(query: str, max_results: int) -> Dict[str, Any]:
    """Search using Serper API"""
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": max_results
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
        
        return {
            "provider": "serper",
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        return {
            "error": f"Serper search failed: {str(e)}"
        }

def _search_duckduckgo(query: str, max_results: int) -> Dict[str, Any]:
    """
    Search using DuckDuckGo (free, no API key needed).
    This is the fallback when no API keys are configured.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Get related topics
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and "Text" in item:
                results.append({
                    "title": item.get("Text", "").split(" - ")[0] if " - " in item.get("Text", "") else "Result",
                    "url": item.get("FirstURL", ""),
                    "snippet": item.get("Text", "")
                })
        
        # If no results from related topics, use abstract
        if not results and data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "url": data.get("AbstractURL", ""),
                "snippet": data.get("Abstract", "")
            })
        
        return {
            "provider": "duckduckgo",
            "query": query,
            "results_count": len(results),
            "results": results,
            "note": "Using free DuckDuckGo API (no key needed)"
        }
    
    except Exception as e:
        return {
            "error": f"DuckDuckGo search failed: {str(e)}",
            "query": query,
            "results": []
        }

if __name__ == "__main__":
    # Run with native SSE transport
    # Binds to 0.0.0.0 for container accessibility
    # Environment variables will be injected by Kubernetes at runtime
    print("=" * 60)
    print("Web Search MCP Server Starting...")
    print(f"Provider: {'Tavily' if TAVILY_API_KEY else 'Serper' if SERPER_API_KEY else 'DuckDuckGo (Free)'}")
    print(f"Max Results: {MAX_RESULTS}")
    print(f"Timeout: {TIMEOUT}s")
    print("=" * 60)
    
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000"))
    )
