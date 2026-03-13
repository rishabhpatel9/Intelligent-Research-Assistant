from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.config import load_config
from src.agents.state import AgentState
from src.agents.nodes.orchestrator import orchestrator_node
from src.agents.nodes.scout import scout_node
from src.agents.nodes.reader import reader_node
from src.agents.nodes.critic import critic_node
from src.agents.nodes.synthesizer import synthesizer_node

# Load config.
load_config()

# Init workflow graph.
graph = StateGraph(AgentState)

# Research nodes.
graph.add_node("orchestrator", orchestrator_node)

def review_plan_node(state: AgentState) -> dict:
    # HITL plan review.
    return {}

graph.add_node("review_plan", review_plan_node)
graph.add_node("scout", scout_node)
graph.add_node("reader", reader_node)
graph.add_node("critic", critic_node)
graph.add_node("synthesis_init", lambda state: {"logs": ["Synthesizer is drafting the final report based on collected data."]})
graph.add_node("synthesizer", synthesizer_node)

graph.set_entry_point("orchestrator")

# Workflow edges.
graph.add_edge("orchestrator", "review_plan")
graph.add_edge("review_plan", "scout")
graph.add_edge("scout", "reader")
graph.add_edge("reader", "critic")

def route_critic(state: AgentState) -> str:
    # Route based on task completion status.
    plan = state.get("plan") or []
    completed_tasks = state.get("completed_tasks") or []
    
    # Verify all tasks completed.
    if len(plan) > 0 and len(completed_tasks) == len(plan):
        return "synthesis_init"
    
    # Retry incomplete tasks.
    return "scout"

graph.add_conditional_edges(
    "critic",
    route_critic,
    {
        "synthesis_init": "synthesis_init",
        "scout": "scout"
    }
)

graph.add_edge("synthesis_init", "synthesizer")

graph.add_edge("synthesizer", END)

memory = MemorySaver()

# Compile with HITL interrupt.
workflow = graph.compile(checkpointer=memory, interrupt_before=["review_plan"])