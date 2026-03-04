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
            "You are a query classifier. "
            "Classify the user query into exactly one of these categories: "
            "search, summarize, factcheck, hybrid. "
            "Respond with only the category name, nothing else."
        )},
        {"role": "user", "content": query}
    ]

    result = query_llm(messages)
    # Normalize output
    return result.strip().lower()