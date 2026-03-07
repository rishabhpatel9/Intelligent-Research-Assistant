from src.tools import search, summarize
from src.llm_client import query_llm

def run(query: str) -> str:
    # If query is too long, treat it as summarize-only
    if len(query.split()) > 20:
        return summarize.run(query)

    search_results = search.run(query)
    
    # Synthesize search results into a detailed report
    messages = [
        {"role": "system", "content": (
            "You are an expert research synthesizer. "
            "Your task is to analyze the provided search results and synthesize a comprehensive, highly structured research report answering the user's query.\n"
            "Format your response with:\n"
            "1. Executive Summary: A high-level overview.\n"
            "2. Deep Dive Analysis: Detailed insights organized with clear headings.\n"
            "3. Key Takeaways: A bulleted list of the most critical points.\n"
            "Ensure the report is objective, well-structured, and strictly uses the provided search results without hallucinating."
        )},
        {"role": "user", "content": f"Query: {query}\n\nSearch Results:\n{search_results}"}
    ]
    
    synthesis = query_llm(messages)

    # Return combined output with proper format
    formatted_output = (
        f"{synthesis}\n\n"
        "**Source References**\n"
        f"{search_results}\n\n"
    )

    return formatted_output