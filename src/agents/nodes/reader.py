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
        
        # Strip non-content elements.
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        
        return text[:3000] 
    except Exception as e:
        return f"[Scrape Error: {str(e)}]"

def reader_node(state: AgentState) -> dict:
    """Iterates over Scout's findings and performs deep scraping on URLs."""
    findings = state.get("research_findings") or []
    
    updated_findings = []
    
    
    for finding in findings:
        if "scraped_data" in finding:
            updated_findings.append(finding)
            continue
            
        raw_data = finding.get("data", "")
        # Scrape web links; keep structured data.
        source = finding.get("source")
        if source in ["duckduckgo", "tavily", "auto"]:
            urls = extract_urls(raw_data)
            
            scraped_content = []
            for url in urls[:2]:
                print(f"[Reader] Deep Scraping: {url}")
                extracted = fetch_and_extract(url)
                scraped_content.append(f"Source: {url}\n{extracted}\n")
            
            finding["scraped_data"] = "\n\n".join(scraped_content)
        else:
            finding["scraped_data"] = finding.get("data", "")
            
        updated_findings.append(finding)
        
    scraped_urls = []
    for f in updated_findings:
        if "scraped_data" in f and f["scraped_data"] != "Not applicable for this source.":
            urls = extract_urls(f.get("data", ""))
            scraped_urls.extend(urls[:2])
            
    node_logs = [f"Reader: Deep scraped {url}" for url in scraped_urls]
    
    return {"research_findings": updated_findings, "logs": node_logs}
