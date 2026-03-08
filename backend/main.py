import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from src.agents.research_agent import workflow

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None

class ApproveRequest(BaseModel):
    thread_id: str
    plan: Optional[list] = None

@app.post("/query")
def run_query(request: QueryRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # We pass the initial state (we need to ensure lists are empty if not provided)
    initial_state = {
        "query": request.query,
        "completed_tasks": [],
        "research_findings": [],
        "messages": [],
        "plan": []
    }
    
    workflow.invoke(initial_state, config=config)
    state = workflow.get_state(config)
    
    if state.next:
        # Paused at 'scout' for HITL
        plan = state.values.get("plan", [])
        return {"status": "requires_approval", "thread_id": thread_id, "plan": plan}
        
    return {"status": "completed", "result": state.values.get("result", "No result generated.")}

@app.post("/approve")
def approve_plan(request: ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # If the user edited the plan on the frontend, update the graph state before resuming
    if request.plan is not None:
        workflow.update_state(config, {"plan": request.plan})
        
    # Resume by passing None to the graph
    workflow.invoke(None, config=config)
    
    state = workflow.get_state(config)
    if not state.next:
        return {"status": "completed", "result": state.values.get("result", "")}
        
    return {"status": "error", "message": f"Graph paused unexpectedly at step: {state.next}. Ensure you don't have interrupt_before set on autonomous loop nodes."}