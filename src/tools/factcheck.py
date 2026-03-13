from src.llm_client import query_llm
from src.tools import search
from src.utils.web_content import fetch_web_content

def run(query: str) -> str:
    # Verify a claim by analyzing information from multiple web sources.
    
    search_results = search.run(query)

    urls = []
    for line in search_results.splitlines():
        if line.strip().startswith("http"):
            urls.append(line.strip())
    urls = urls[:4]

    evidence_texts = []
    for url in urls:
        content = fetch_web_content(url)
        evidence_texts.append(f"Source: {url}\n{content}")

    combined_evidence = "\n\n".join(evidence_texts)

    messages = [
        {"role": "system", "content": (
            "You are a rigorous, objective fact checking assistant. "
            "Given the following claim and supporting evidence from multiple web sources, "
            "determine whether the claim is likely 'True', 'False', or 'Uncertain' based strictly on the evidence provided. "
            "Format your response as a professional, publication ready structured report:\n"
            "1. Verdict: [True/False/Uncertain]\n"
            "2. Evidence Summary: (A concise bulleted list of key findings supporting the verdict, with citations)\n"
            "3. Conclusion: (A brief concluding sentence)"
        )},
        {"role": "user", "content": f"Claim: {query}\n\nEvidence:\n{combined_evidence}"}
    ]

    analysis = query_llm(messages)

    formatted_output = (
        "**Evidence Gathered (Top 4 Sources)**\n"
        f"{combined_evidence}\n\n"
        "**FactCheck Verdict**\n"
        f"{analysis}"
    )

    return formatted_output