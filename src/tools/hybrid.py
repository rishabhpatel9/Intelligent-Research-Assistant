from src.tools import search, summarize

def run(query: str) -> str:
    # Runs search first, then summarizes the results for queries that need both retrieval and synthesis.

    # Step 1: Run search
    search_results = search.run(query)

    # Step 2: Pass search results into summarizer
    summary = summarize.run(search_results)

    # Step 3: Return combined output with proper format
    formatted_output = (
        "**Summary**\n"
        f"{summary}"
        "**Search Results (Top Sources)**\n"
        f"{search_results}\n\n"
    )

    return formatted_output
