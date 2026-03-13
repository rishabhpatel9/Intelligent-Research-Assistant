from src.agents.state import AgentState
from src.tools.search import run as omni_search

def scout_node(state: AgentState) -> dict:
    # Search for information based on the research plan.
    plan = state.get("plan") or []
    completed_tasks = state.get("completed_tasks") or []
    
    new_findings = []
    new_completed = []
    
    for task in plan:
        task_id = task.get("id")
        if task_id in completed_tasks:
            continue
            
        description = task.get("description")
        source = task.get("source", "auto")
        
        print(f"[Scout] Executing query: '{description}' via source: {source}")
        
        try:
            raw_result = omni_search(description, source=source)
            finding = {
                "task_id": task_id,
                "query": description,
                "source": source,
                "data": raw_result
            }
            new_findings.append(finding)
            new_completed.append(task_id)
        except Exception as e:
            print(f"[Scout] Error executing task {task_id}: {e}")
            # Skip marking as complete on failure to allow for retries.
            
    node_logs = []
    for f in new_findings:
        node_logs.append(f"Scout: Investigated '{f['query']}' via {f['source']}.")
        
    return {"research_findings": new_findings, "completed_tasks": new_completed, "logs": node_logs}
