from src.llm_client import query_llm
from src.tools import search

def run(query: str) -> str:
    # Verifies whether a claim is true or false. Uses search results for evidence, then asks LLM to reason.
    
    # Step 1: Run search to gather evidence
    search_results = search.run(query)

    # Step 2: Pass on to LLM to analyze evidence
    messages = [
        {"role": "system", "content": (
            "You are a fact checking assistant. "
            "Given the following claim and supporting search results, "
            "determine whether the claim is likely true, false, or uncertain. "
            "Explain very briefly, citing evidence from the results."
        )},
        {"role": "user", "content": f"Claim: {query}\n\nEvidence:\n{search_results}"}
    ]

    analysis = query_llm(messages)

    # Step 3: Format output
    formatted_output = (
        "**Evidence Gathered**\n"
        f"{search_results}\n\n"
        "**FactCheck Result**\n"
        f"{analysis}"
    )

    return formatted_output
