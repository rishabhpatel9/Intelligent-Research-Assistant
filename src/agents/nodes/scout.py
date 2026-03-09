from src.agents.state import AgentState
from src.tools.search import run as omni_search

def scout_node(state: AgentState):
    # Executes the research plan using the Omni_Search tool.
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
        
        yield {"logs": [f"Scout: Investigating '{description}' via {source}..."]}
        
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
            yield {"logs": [f"Scout: Error investigating '{task_id}': {str(e)}"]}
            
    yield {
        "research_findings": new_findings, 
        "completed_tasks": new_completed, 
        "logs": [f"Scout: Completed {len(new_completed)} research tasks."]
    }

