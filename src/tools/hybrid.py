from src.tools import search, summarize

def run(query: str) -> str:
    # If query is too long, treat it as summarize-only
    if len(query.split()) > 20:
        return summarize.run(query)

    search_results = search.run(query)
    summary = summarize.run(search_results)

    # Step 3: Return combined output with proper format
    formatted_output = (
        "**Summary**\n"
        f"{summary}\n\n"
        "**Search Results (Top Sources)**\n"
        f"{search_results}\n\n"
    )

    return formatted_output