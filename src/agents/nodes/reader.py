import requests
import re
from bs4 import BeautifulSoup
from src.agents.state import AgentState

def extract_urls(text: str) -> list:
    """Extract standard http/https URLs from a string."""
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    return url_pattern.findall(text)

def fetch_and_extract(url: str) -> str:
    """Simple deep scraping: fetch URL and extract main text."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove noisy elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        # Compress whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Return first 3000 characters to avoid entirely blowing up LLM context
        return text[:3000] 
    except Exception as e:
        return f"[Scrape Error: {str(e)}]"

def reader_node(state: AgentState) -> dict:
    """Iterates over Scout's findings and performs deep scraping on URLs."""
    findings = state.get("research_findings") or []
    
    updated_findings = []
    
    # We only want to scrape newly added findings. For simplicity in this iteration, 
    # we just check if 'scraped_data' key exists on the finding.
    
    for finding in findings:
        if "scraped_data" in finding:
            updated_findings.append(finding)
            continue
            
        raw_data = finding.get("data", "")
        # Deep scraping is mainly targeted at general web search results.
        # For structured sources like Wikipedia/ArXiv we keep the original data.
        source = finding.get("source")
        if source in ["duckduckgo", "tavily", "auto"]:
            urls = extract_urls(raw_data)
            
            scraped_content = []
            # Scrape up to 2 URLs per finding to save time/context
            for url in urls[:2]:
                print(f"[Reader] Deep Scraping: {url}")
                extracted = fetch_and_extract(url)
                scraped_content.append(f"Source: {url}\n{extracted}\n")
            
            # Append scraped data to the finding
            finding["scraped_data"] = "\n\n".join(scraped_content)
        else:
            # Not a standard web result, no deep scrape needed; preserve the
            # original content so downstream nodes (e.g. Critic) see real data
            # instead of a placeholder string.
            finding["scraped_data"] = finding.get("data", "")
            
        updated_findings.append(finding)
        
    scraped_urls = []
    for f in updated_findings:
        if "scraped_data" in f and f["scraped_data"] != "Not applicable for this source.":
            # Extract URLs from the scraped content for logging
            urls = extract_urls(f.get("data", ""))
            scraped_urls.extend(urls[:2])
            
    node_logs = [f"Reader: Deep scraped {url}" for url in scraped_urls]
    
    # Return it to comply with LangGraph structure
    return {"research_findings": updated_findings, "logs": node_logs}
