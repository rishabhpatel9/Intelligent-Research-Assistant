from src.llm_client import query_llm

def run(query: str) -> str:
    """
    Summarize given text (snippets, headlines, or article content) using LM Studio.
    """
    messages = [
        {"role": "system", "content": (
            "You are a summarizer. Condense the following content into a clear, concise overview. "
            "Focus on the main themes and avoid repetition."
        )},
        {"role": "user", "content": query}
    ]

    return query_llm(messages)

# yet to add fetch_web_content for better summaries if snippets don't have enough context