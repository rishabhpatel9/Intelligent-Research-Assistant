from src.tools import search, summarize

def run(query: str) -> str:
    # Runs search first, then summarizes the results for queries that need both retrieval and synthesis.
    
    # Step 1: Run search
    search_results = search.run(query)

    # Step 2: Pass search results into summarizer
    summary = summarize.run(search_results)

    # Step 3: Return combined output
    return f"Search Results:\n{search_results}\n\nSummary:\n{summary}"