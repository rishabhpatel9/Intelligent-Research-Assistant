from typing import TypedDict
from src.config import load_config
from src.llm_client import query_llm
from langgraph.graph import StateGraph, END
from src.tools import search, summarize, factcheck, hybrid

# Load environment variables (including LangSmith settings)
load_config()


def classify_query_llm(query: str) -> str:
    # Classify user query into exactly one category
    messages = [
        {"role": "system", "content": (
            "You are a strict, precise query classifier. "
            "Classify the user query into exactly ONE of these 4 categories: "
            "'search', 'summarize', 'factcheck', 'hybrid'. "
            "Rules:\n"
            "- 'factcheck' : query asks whether something is true/false, requests verification, or asks 'Is it true that...'\n"
            "- 'summarize' : query asks to condense, shorten, or summarize text that is provided or referenced\n"
            "- 'hybrid' : query asks for deep comparison, pros/cons, or complex analysis across multiple facets\n"
            "- 'search' : query asks for general knowledge, current events, latest info, 'who', 'what', or 'when'\n"
            "CRITICAL: Respond ONLY with the exact single word matching the category ('search', 'summarize', 'factcheck', or 'hybrid'). Do not include any punctuation or extra text."
        )},
        {"role": "user", "content": query}
    ]

    result = query_llm(messages)
    # Normalize output
    category = result.strip().lower()
    
    if "factcheck" in category:
        return "factcheck"
    elif "summarize" in category:
        return "summarize"
    elif "hybrid" in category:
        return "hybrid"
    
    return "search"

def classify_query(query: str) -> str:
    # Force summarize for long queries to avoid search API errors
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