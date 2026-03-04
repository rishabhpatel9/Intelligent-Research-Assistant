from src.llm_client import query_llm

def run(text: str) -> str:
    """
    Summarize given text (snippets, headlines, or article content).
    Handles cases where context is minimal by producing a thematic overview.
    """
    # Decide if there is enough context
    if len(text.strip()) < 50:  # arbitrary threshold for "short input"
        system_prompt = (
            "You are a summarizer. The user has provided limited context "
            "(mostly headlines or short snippets). "
            "Instead of a detailed summary, produce a high level overview "
            "of the main themes or topics implied by the sources."
        )
    else:
        system_prompt = (
            "You are a summarizer. Condense the following content into a clear, concise overview. "
            "Focus on the main themes and avoid repetition."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    return query_llm(messages)