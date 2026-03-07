from src.llm_client import query_llm

def run(text: str) -> str:
    # Produce thematic overview for short text or detailed summary for long text
    
    # Use threshold to decide summary type
    if len(text.strip()) < 50:
        system_prompt = (
            "You are an expert summarizer. The user has provided limited context "
            "(mostly headlines or short snippets). "
            "Produce a highly structured, professional overview of the main themes implied by the sources.\n"
            "Format your response with an **Executive Summary** followed by **Key Themes** (bullet points)."
        )
    else:
        system_prompt = (
            "You are an expert summarizer. Condense the following content into a highly structured, professional overview.\n"
            "Format your response with an **Executive Summary** (2-3 sentences) followed by **Key Highlights** (bullet points).\n"
            "Ensure the output looks polished, well laid out, and ready for a formal report."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    return query_llm(messages)