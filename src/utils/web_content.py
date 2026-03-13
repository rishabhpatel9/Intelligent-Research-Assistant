import requests
from bs4 import BeautifulSoup

def fetch_web_content(url: str) -> str:
    # Extract readable text from a webpage and return a cleaned string.
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = [p.get_text() for p in soup.find_all("p")]
        text = "\n".join(paragraphs)

        # Limit output length to conserve context.
        return text[:2000] if text else "[No readable content found]"
    except Exception as e:
        return f"[Error fetching {url}: {str(e)}]"