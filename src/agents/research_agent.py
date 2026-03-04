from src.llm_client import query_llm

def classify_query_llm(query: str) -> str:
    """
    Classify the user query into one of four categories:
    - "search"
    - "summarize"
    - "factcheck"
    - "hybrid"

    Args:
        query (str): The user input query

    Returns:
        str: One of the categories above
    """
    messages = [
        {"role": "system", "content": (
            "You are a strict query classifier. "
            "Classify the user query into exactly one of these categories: "
            "search, summarize, factcheck, hybrid. "
            "Rules:\n"
            "- If the query asks whether something is true/false, requests verification, or asks 'Is it true that...' → factcheck\n"
            "- If the query asks to condense, shorten, or summarize text → summarize\n"
            "- If the query asks for comparison, pros/cons, or analysis across options → hybrid\n"
            "- If the query asks for current, latest, or recent info → search\n"
            "Important: Always choose factcheck for verification-style queries, even if they could also involve searching. "
            "Respond with only the category name, nothing else."
        )},
        {"role": "user", "content": query}
    ]

    result = query_llm(messages)
    # Normalize output
    return result.strip().lower()