import requests
import re
import io
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from src.agents.state import AgentState

def extract_urls(text: str) -> list:
    """Extract standard http/https URLs from a string."""
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    return url_pattern.findall(text)

def fetch_and_extract(url: str) -> str:
    """Simple deep scraping: fetch URL and extract main text (HTML or PDF)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/pdf,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Handle PDF
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            try:
                with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    return text[:5000] # Increased limit for PDFs as they are often denser
            except Exception as pdf_err:
                return f"[PDF Parse Error: {str(pdf_err)}]"
        
        # Handle HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strip non-content elements.
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        
        return text[:3000] 
    except requests.exceptions.HTTPError as e:
        return f"[HTTP Error {e.response.status_code}: {url}]"
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
