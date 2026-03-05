from src.llm_client import query_llm
from src.tools import search
from src.utils.web_content import fetch_web_content

def run(query: str) -> str:
    # Verifies whether a claim is true or false. Fetches full content from top 4 search results, then asks LLM to analyze.
    
    # Step 1: Run search
    search_results = search.run(query)

    # Step 2: Extract top 4 URLs
    urls = []
    for line in search_results.splitlines():
        if line.startswith("http"):
            urls.append(line.strip())
    urls = urls[:4]

    # Step 3: Fetch content
    evidence_texts = []
    for url in urls:
        content = fetch_web_content(url)
        evidence_texts.append(f"Source: {url}\n{content}")

    combined_evidence = "\n\n".join(evidence_texts)

    # Step 4: Ask LLM to analyze
    messages = [
        {"role": "system", "content": (
            "You are a fact checking assistant. "
            "Given the following claim and supporting evidence from multiple sources, "
            "determine whether the claim is likely True, False, or Uncertain. "
            "Provide a clear verdict followed by a very short and concise explanation."
        )},
        {"role": "user", "content": f"Claim: {query}\n\nEvidence:\n{combined_evidence}"}
    ]

    analysis = query_llm(messages)

    # Step 5: Format output
    formatted_output = (
        "**Evidence Gathered (Top 4 Sources)**\n"
        f"{combined_evidence}\n\n"
        "**FactCheck Verdict**\n"
        f"{analysis}"
    )

    return formatted_output