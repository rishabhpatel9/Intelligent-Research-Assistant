import operator
from typing import TypedDict, Annotated, List, Dict, Any

class AgentState(TypedDict):
    # State object for the research workflow.
    query: str
    category: str
    plan: List[Dict[str, Any]]
    research_findings: Annotated[List[Dict[str, Any]], operator.add]
    completed_tasks: Annotated[List[str], operator.add]
    result: str
    messages: Annotated[List[Dict[str, Any]], operator.add]
    logs: Annotated[List[str], operator.add]
