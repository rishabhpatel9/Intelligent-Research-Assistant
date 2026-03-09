import operator
from typing import TypedDict, Annotated, List, Dict, Any

class AgentState(TypedDict):
    # Agent state for the multi-hop research graph.
    query: str # Original user query
    category: str # Routing category
    plan: List[Dict[str, Any]] # Scheduled research tasks
    research_findings: Annotated[List[Dict[str, Any]], operator.add] # Gathered data
    completed_tasks: Annotated[List[str], operator.add] # Finished tasks
    result: str # Final synthesized output
    messages: Annotated[List[Dict[str, Any]], operator.add] # Message history
    logs: Annotated[List[str], operator.add] # Detailed agent action logs
