def classify_query(query: str) -> str:
    """
    Classify the user query into one of four categories:
    - "search": needs fresh info from the web
    - "summarize": summarization of provided text/documents
    - "factcheck": verifying a claim
    - "hybrid": ambiguous or multi-step queries

    Args:
        query (str): The user input query

    Returns:
        str: One of ["search", "summarize", "factcheck", "hybrid"]
    """
    q_lower = query.lower()

    # keyword based rules
    if any(word in q_lower for word in ["latest", "current", "recent", "update", "news"]):
        return "search"
    elif any(word in q_lower for word in ["summarize", "overview", "condense", "shorten"]):
        return "summarize"
    elif any(word in q_lower for word in ["true", "false", "verify", "fact", "accurate", "check"]):
        return "factcheck"
    elif any(word in q_lower for word in ["compare", "analyze", "pros and cons", "versus"]):
        return "hybrid"
    # Default fallback
    else:
        return "hybrid"
