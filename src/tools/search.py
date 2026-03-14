import os
import sqlite3
import hashlib
import json
import requests
from ddgs import DDGS
import wikipedia
import arxiv
import time
from datetime import datetime, timedelta

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"

# Initialize search result SQLite cache with TTL support.
CACHE_DB = "search_cache.db"
def init_cache():
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    # Migration: Add timestamp if it doesn't exist
    c.execute("PRAGMA table_info(search_cache)")
    columns = [row[1] for row in c.fetchall()]
    if not columns:
        c.execute('''CREATE TABLE IF NOT EXISTS search_cache
                     (query_hash TEXT PRIMARY KEY, query TEXT, source TEXT, result TEXT, timestamp DATETIME)''')
    elif "timestamp" not in columns:
        print("[Cache] Migrating database to add timestamp column...")
        c.execute("ALTER TABLE search_cache ADD COLUMN timestamp DATETIME")
    conn.commit()
    conn.close()

init_cache()

def get_cache(query: str, source: str, ttl_hours: int = None) -> str:
    query_hash = hashlib.sha256(f"{source}:{query.lower().strip()}".encode()).hexdigest()
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("SELECT result, timestamp FROM search_cache WHERE query_hash=?", (query_hash,))
    row = c.fetchone()
    conn.close()
    
    if row:
        result, ts_str = row
        if ttl_hours and ts_str:
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > ts + timedelta(hours=ttl_hours):
                    return None # Cache expired
            except Exception:
                return None
        return result
    return None

def set_cache(query: str, source: str, result: str):
    query_hash = hashlib.sha256(f"{source}:{query.lower().strip()}".encode()).hexdigest()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(CACHE_DB)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO search_cache (query_hash, query, source, result, timestamp) VALUES (?, ?, ?, ?, ?)", 
              (query_hash, query, source, result, ts))
    conn.commit()
    conn.close()

def is_realtime_query(query: str) -> bool:
    """Detect if the query asks for live or highly recent information."""
    rt_keywords = ["today", "now", "live", "results", "price", "stock", "trending", "current", "latest"]
    q_lower = query.lower()
    return any(kw in q_lower for kw in rt_keywords)

def search_duckduckgo(query: str, timelimit: str = None) -> str:
    try:
        results = DDGS().text(query, max_results=3, timelimit=timelimit)
        if not results: return None
        formatted = "\n".join([f"- {r['title']}\n  {r['body']}\n  {r['href']}" for r in results])
        return formatted
    except Exception:
        return None

def search_wikipedia(query: str) -> str:
    try:
        # Fetch a concise summary from Wikipedia.
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True, redirect=True)
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

def search_tavily(query: str, depth: str = "basic") -> str:
    if not TAVILY_API_KEY:
        return None
    try:
        # Tavily is premium; returns higher quality snippets.
        payload = {"api_key": TAVILY_API_KEY, "query": query, "num_results": 3, "search_depth": depth}
        response = requests.post(TAVILY_URL, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()
        results = []
        for item in data.get("results", []):
            results.append(f"- {item.get('title')}\n  {item.get('snippet')}\n  {item.get('url')}")
        return "\n".join(results) if results else None
    except Exception as e:
        print(f"[SearchLog] Tavily error: {e}")
        return None

def run(query: str, source="auto", timelimit: str = None) -> str:
    # Identify if the query is real-time/high-freshness.
    realtime = is_realtime_query(query)
    if realtime:
        print(f"[SearchTriage] Real time query detected: '{query}'")

    # Use 1 hour TTL for real-time queries, 24 hours for others.
    ttl = 1 if realtime else 24

    # Search across multiple platforms with automatic fallback.
    cached = get_cache(query, source, ttl_hours=ttl)
    if cached:
        return f"[Cached {source}] \n{cached}"

    result = None
    applied_source = source
    tavily_depth = "advanced" if realtime else "basic"

    if source == "wikipedia":
        # Search Wikipedia with fallback to general web search.
        result = search_wikipedia(query)
        if not result:
            applied_source = "duckduckgo"
            result = search_duckduckgo(query, timelimit=timelimit)
    elif source == "arxiv":
        # Search ArXiv with fallback to general web search.
        result = search_arxiv(query)
        if not result:
            applied_source = "duckduckgo"
            result = search_duckduckgo(f"{query} arxiv", timelimit=timelimit)
    elif source == "tavily":
        result = search_tavily(query, depth=tavily_depth)
    elif source == "duckduckgo":
        result = search_duckduckgo(query, timelimit=timelimit)
    else:
        # Smart "auto" routing: Prioritize Tavily for real-time queries.
        if realtime:
            applied_source = "tavily"
            result = search_tavily(query, depth=tavily_depth)
            if not result:
                applied_source = "duckduckgo"
                result = search_duckduckgo(query, timelimit=timelimit)
        else:
            applied_source = "duckduckgo"
            result = search_duckduckgo(query, timelimit=timelimit)
            if not result:
                applied_source = "tavily"
                result = search_tavily(query, depth=tavily_depth)

    if result:
        set_cache(query, applied_source, result)
        return f"[{applied_source.capitalize()} Results]\n{result}"
    
    return "[Search] No results found across available engines."
