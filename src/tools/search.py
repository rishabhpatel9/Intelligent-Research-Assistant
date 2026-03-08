import os
import sqlite3
import hashlib
import json
import requests
from duckduckgo_search import DDGS
import wikipedia
import arxiv

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"

# Setup SQLite Cache
CACHE_DB = "search_cache.db"
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                 (query_hash TEXT PRIMARY KEY, query TEXT, source TEXT, result TEXT)''')
    conn.commit()
    conn.close()

init_cache()

def get_cache(query: str, source: str) -> str:
    query_hash = hashlib.sha256(f"{source}:{query.lower().strip()}".encode()).hexdigest()
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT result FROM search_cache WHERE query_hash=?", (query_hash,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_cache(query: str, source: str, result: str):
    query_hash = hashlib.sha256(f"{source}:{query.lower().strip()}".encode()).hexdigest()
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?, ?)", 
              (query_hash, query, source, result))
    conn.commit()
    conn.close()

def search_duckduckgo(query: str) -> str:
    try:
        results = DDGS().text(query, max_results=3)
        if not results: return None
        formatted = "\n".join([f"- {r['title']}\n  {r['body']}\n  {r['href']}" for r in results])
        return formatted
    except Exception:
        return None

def search_wikipedia(query: str) -> str:
    try:
        # Get top 2 sentences of summary
        summary = wikipedia.summary(query, sentences=3, auto_suggest=False)
        return f"- Wikipedia: {query}\n  {summary}"
    except Exception:
        return None

def search_arxiv(query: str) -> str:
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=2, sort_by=arxiv.SortCriterion.Relevance)
        results = list(client.results(search))
        if not results: return None
        formatted = "\n".join([f"- {r.title}\n  {r.summary[:300]}...\n  {r.entry_id}" for r in results])
        return formatted
    except Exception:
        return None

def search_tavily(query: str) -> str:
    if not TAVILY_API_KEY:
        return None
    try:
        payload = {"api_key": TAVILY_API_KEY, "query": query, "num_results": 3}
        response = requests.post(TAVILY_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            results.append(f"- {item.get('title')}\n  {item.get('snippet')}\n  {item.get('url')}")
        return "\n".join(results) if results else None
    except Exception:
        return None

def run(query: str, source="auto") -> str:
    
    # Omni-Search implementation. Source options: auto, duckduckgo, wikipedia, arxiv, tavily
    # Check cache first
    cached = get_cache(query, source)
    if cached:
        return f"[Cached {source}] \n{cached}"

    result = None
    applied_source = source

    if source == "wikipedia":
        result = search_wikipedia(query)
    elif source == "arxiv":
        result = search_arxiv(query)
    elif source == "tavily":
        result = search_tavily(query)
    elif source == "duckduckgo":
        result = search_duckduckgo(query)
    else:
        # "auto" fallback routing
        applied_source = "duckduckgo"
        result = search_duckduckgo(query)
        if not result: # Fallback to Tavily
            applied_source = "tavily"
            result = search_tavily(query)

    if result:
        set_cache(query, applied_source, result)
        return f"[{applied_source.capitalize()} Results]\n{result}"
    
    return "[Search] No results found across available engines."