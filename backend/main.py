import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Set
from src.agents.research_agent import workflow
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
cancelled_threads: Set[str] = set()

class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None

class ApproveRequest(BaseModel):
    thread_id: str
    plan: Optional[list] = None

class CancelRequest(BaseModel):
    thread_id: str

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
                # Check for external cancellation request
                if request.thread_id in cancelled_threads:
                    cancelled_threads.discard(request.thread_id)
                    yield f"data: {json.dumps({'status': 'cancelled', 'thread_id': request.thread_id})}\n\n"
                    break
                if chunk:
                    node_name = list(chunk.keys())[0]
                    node_data = chunk[node_name]
                    
                    # 1. Yield the generic "starting" message as a step_start event
                    event_type = "step_start"
                    msg = f"Agent '{node_name.capitalize()}' is processing..."
                    if node_name == "scout":
                        msg = "Searching for background info"
                    elif node_name == "reader":
                        msg = "Deep scraping sources"
                    elif node_name == "critic":
                        msg = "Verifying if data is useful"
                    elif node_name == "synthesis_init":
                        msg = "Completing your homework"
                    elif node_name == "synthesizer":
                        msg = "Check out the report!"
                    
                    yield f"data: {json.dumps({'event': 'step_start', 'node': node_name, 'message': msg})}\n\n"
                    
                    # 2. Yield detailed logs returned by the node, batched to avoid UI thrashing
                    if isinstance(node_data, dict) and "logs" in node_data:
                        logs = node_data.get("logs") or []
                        if logs:
                            combined_log = "\n".join(logs)
                            yield f"data: {json.dumps({'event': 'step_log', 'node': node_name, 'log': combined_log})}\n\n"
                    
            state = workflow.get_state(config)
            vals = state.values or {}
            if not state.next:
                final_result = vals.get("result", "")
                yield f"data: {json.dumps({'status': 'completed', 'result': final_result})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': f'Paused at {state.next}'})}\n\n"
        except Exception as e:
            logger.exception("Error in event_generator stream")
            yield f"data: {json.dumps({'status': 'error', 'message': 'An unexpected error occurred during processing. Please check the logs.'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/cancel")
def cancel_run(request: CancelRequest):
    """Mark a thread as cancelled so any active stream can stop early."""
    cancelled_threads.add(request.thread_id)
    return {"status": "cancelled", "thread_id": request.thread_id}