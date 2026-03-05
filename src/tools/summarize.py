from src.llm_client import query_llm

def run(text: str) -> str:
    # Summarize given text (snippets, headlines, or article content).
    # Handles cases where context is minimal by producing a thematic overview.
    
    # Decide if there is enough context (arbitrary threshold for "short input")
    if len(text.strip()) < 50:
        system_prompt = (
            "You are a summarizer. The user has provided limited context "
            "(mostly headlines or short snippets). "
            "Produce a high-level overview of the main themes implied by the sources."
        )
    else:
        system_prompt = (
            "You are a summarizer. Condense the following content into a clear, concise overview. "
            "Focus on the main themes and avoid repetition."
            "Limit your response to 4–5 sentences."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    return query_llm(messages)