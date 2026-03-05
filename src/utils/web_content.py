import requests
from bs4 import BeautifulSoup

def fetch_web_content(url: str) -> str:
    # Fetch and extract readable text content from a webpage.
    # Returns a cleaned string of text (truncated for safety).
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract visible text from <p> tags
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        text = "\n".join(paragraphs)

        # Truncate to avoid token overload
        return text[:2000] if text else "[No readable content found]"
    except Exception as e:
        return f"[Error fetching {url}: {str(e)}]"