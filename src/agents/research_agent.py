from src.llm_client import query_llm
from langgraph.graph import StateGraph, END
from src.tools import search, summarize, factcheck, hybrid

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
            "You are a strict query classifier. "
            "Classify the user query into exactly one of these categories: "
            "search, summarize, factcheck, hybrid. "
            "Rules:\n"
            "- If the query asks whether something is true/false, requests verification, or asks 'Is it true that...' → factcheck\n"
            "- If the query asks to condense, shorten, or summarize text → summarize\n"
            "- If the query asks for comparison, pros/cons, or analysis across options → hybrid\n"
            "- If the query asks for current, latest, or recent info → search\n"
            "Important: Always choose factcheck for verification-style queries, even if they could also involve searching. "
            "Respond with only the category name, nothing else."
        )},
        {"role": "user", "content": query}
    ]

    result = query_llm(messages)
    # Normalize output
    return result.strip().lower()

# Define the state
class AgentState(dict):
    pass

def classify_node(state: AgentState) -> str:
    query = state["query"]
    category = classify_query_llm(query)
    state["category"] = category
    return category

def search_node(state: AgentState) -> str:
    result = search.run(state["query"])
    state["result"] = result
    return END

def summarize_node(state: AgentState) -> str:
    result = summarize.run(state["query"])
    state["result"] = result
    return END

def factcheck_node(state: AgentState) -> str:
    result = factcheck.run(state["query"])
    state["result"] = result
    return END

def hybrid_node(state: AgentState) -> str:
    result = hybrid.run(state["query"])
    state["result"] = result
    return END

# Build the graph
graph = StateGraph(AgentState)

graph.add_node("classify", classify_node)
graph.add_node("search", search_node)
graph.add_node("summarize", summarize_node)
graph.add_node("factcheck", factcheck_node)
graph.add_node("hybrid", hybrid_node)

graph.set_entry_point("classify")

graph.add_edge("classify", "search")
graph.add_edge("classify", "summarize")
graph.add_edge("classify", "factcheck")
graph.add_edge("classify", "hybrid")

workflow = graph.compile()