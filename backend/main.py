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
        "category": "",
        "plan": [],
        "research_findings": [],
        "completed_tasks": [],
        "messages": [],
        "logs": []
    }
    
    workflow.invoke(initial_state, config=config)
    state = workflow.get_state(config)
    
    if state.next:
        # Paused at 'review_plan' for HITL
        vals = state.values or {}
        plan = vals.get("plan") or []
        initial_logs = vals.get("logs") or []
        return {"status": "requires_approval", "thread_id": thread_id, "plan": plan, "logs": initial_logs}
        
    return {"status": "completed", "result": state.values.get("result", "No result generated.")}

from fastapi.responses import StreamingResponse
import json

@app.post("/approve")
async def approve_plan(request: ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    
    if request.plan is not None:
        workflow.update_state(config, {"plan": request.plan})
        
    def event_generator():
        try:
            # Stream the events from the compiled LangGraph workflow
            # Using stream_mode="values" or "updates"
            for chunk in workflow.stream(None, config=config, stream_mode="updates"):
                if chunk:
                    node_name = list(chunk.keys())[0]
                    node_data = chunk[node_name]
                    
                    # 1. Yield the generic "starting" message as a step_start event
                    event_type = "step_start"
                    msg = f"Agent '{node_name.capitalize()}' is processing..."
                    if node_name == "scout":
                        msg = "Searching for background info..."
                    elif node_name == "reader":
                        msg = "Deep-scraping selected sources..."
                    elif node_name == "critic":
                        msg = "Verifying if data fulfills the plan..."
                    elif node_name == "synthesizer":
                        msg = "Drafting the final report..."
                    
                    yield f"data: {json.dumps({'event': 'step_start', 'node': node_name, 'message': msg})}\n\n"
                    
                    # 2. Yield any detailed logs returned by the node itself
                    if isinstance(node_data, dict) and "logs" in node_data:
                        logs = node_data.get("logs") or []
                        for log_entry in logs:
                            yield f"data: {json.dumps({'event': 'step_log', 'node': node_name, 'log': log_entry})}\n\n"
                    
            state = workflow.get_state(config)
            vals = state.values or {}
            if not state.next:
                final_result = vals.get("result", "")
                yield f"data: {json.dumps({'status': 'completed', 'result': final_result})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': f'Paused at {state.next}'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")