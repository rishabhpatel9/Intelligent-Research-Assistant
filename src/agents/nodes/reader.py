import requests
import re
import io
import fitz  # PyMuPDF
import random
from bs4 import BeautifulSoup
from src.agents.state import AgentState

def extract_urls(text: str) -> list:
    # Extract standard http/https URLs from a string.
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    return url_pattern.findall(text)

def get_stealth_headers():
    # Returns randomized browser like headers to bypass simple bot detection.
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/pdf,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1'
    }

def fetch_and_extract(url: str) -> str:
    # Simple deep scraping: fetch URL and extract main text (HTML or PDF).
    try:
        headers = get_stealth_headers()
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Handle PDF
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            try:
                with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
                    text = ""
                    # Read up to first 10 pages for better context balance
                    for page in doc[:10]:
                        text += page.get_text()
                    return text[:8000] # Increased limit for PDFs
            except Exception as pdf_err:
                return f"[PDF Parse Error: {str(pdf_err)}]"
        
        # Handle HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strip noise elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "ad", "noscript"]):
            element.decompose()
            
        # Try to find the main content area to reduce noise
        main_content = soup.find('main') or soup.find('article') or soup.find('div', id=re.compile(r'content|main|article', re.I)) or soup.body
        if not main_content:
            return "[Scrape Error: No usable content area found]"

        # Remove noisy attributes from all tags in the main content
        for tag in main_content.find_all(True):
            tag.attrs = {key: value for key, value in tag.attrs.items() if key.lower() not in ['id', 'class', 'style', 'onclick']}

        # Extract text while preserving structural markers (like newlines for headers/lists) and manually process some tags to add semantic spacing
        for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li']):
            tag.insert_before('\n')
            tag.insert_after('\n')

        text = main_content.get_text(separator=' ', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text) # Clean up multiple newlines
        text = re.sub(r' +', ' ', text) # Clean up extra spaces
        
        return text[:4500] # Slightly increased limit for cleaner content
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
