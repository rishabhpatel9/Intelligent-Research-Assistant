from typing import TypedDict
from src.config import load_config
from src.llm_client import query_llm
from langgraph.graph import StateGraph, END
from src.tools import search, summarize, factcheck, hybrid

# Load environment variables (including LangSmith settings)
load_config()


def classify_query_llm(query: str) -> str:
    # Classify the user query into one of four categories and returns str: One of the categories
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
    category = result.strip().lower()

    if category not in ["search", "summarize", "factcheck", "hybrid"]:
        return "search"
        
    return category

def classify_query(query: str) -> str:
    # If the query contains a long block of text, force summarize 
    # to prevent sending huge text blocks to search APIs (which causes errors).
    if len(query.split()) > 50:
        return "summarize"
    return classify_query_llm(query)

# Define the state
class AgentState(TypedDict):
    query: str
    category: str
    result: str

def classify_node(state: AgentState) -> dict:
    query = state["query"]
    category = classify_query(query)
    return {"category": category}

def search_node(state: AgentState) -> dict:
    result = search.run(state["query"])
    return {"result": result}

def summarize_node(state: AgentState) -> dict:
    result = summarize.run(state["query"])
    return {"result": result}

def factcheck_node(state: AgentState) -> dict:
    result = factcheck.run(state["query"])
    return {"result": result}

def hybrid_node(state: AgentState) -> dict:
    result = hybrid.run(state["query"])
    return {"result": result}

# Build the graph
graph = StateGraph(AgentState)

graph.add_node("classify", classify_node)
graph.add_node("search", search_node)
graph.add_node("summarize", summarize_node)
graph.add_node("factcheck", factcheck_node)
graph.add_node("hybrid", hybrid_node)

graph.set_entry_point("classify")

def route_query(state: AgentState) -> str:
    return state["category"]

graph.add_conditional_edges(
    "classify",
    route_query,
    {
        "search": "search",
        "summarize": "summarize",
        "factcheck": "factcheck",
        "hybrid": "hybrid",
    }
)

graph.add_edge("search", END)
graph.add_edge("summarize", END)
graph.add_edge("factcheck", END)
graph.add_edge("hybrid", END)

workflow = graph.compile()