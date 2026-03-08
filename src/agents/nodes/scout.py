from src.agents.state import AgentState
from src.tools.search import run as omni_search

def scout_node(state: AgentState) -> dict:
    # Executes the research plan using the Omni_Search tool.
    plan = state.get("plan", [])
    completed_tasks = state.get("completed_tasks", [])
    
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
            # Do not mark as complete if there's a hard crash, Critics might retry
            
    return {"research_findings": new_findings, "completed_tasks": new_completed}
