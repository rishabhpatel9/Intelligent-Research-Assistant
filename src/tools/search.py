import requests
import os

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"

def run(query: str) -> str:
    
    # Perform a web search using Tavily API. Returns a formatted string of results.
    if not TAVILY_API_KEY:
        return "[Search Error] Tavily API key not set."

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "num_results": 3
    }

    try:
        response = requests.post(TAVILY_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            title = item.get("title", "No title")
            url = item.get("url", "No URL")
            snippet = item.get("snippet", "")
            results.append(f"- {title}\n  {snippet}\n  {url}")

        return "\n".join(results) if results else "[Search] No results found."
    except Exception as e:
        return f"[Search Error] {str(e)}"