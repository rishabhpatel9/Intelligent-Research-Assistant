from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly

def critic_node(state: AgentState):
    # Evaluates if the collected findings are sufficient for a given task.
    plan = state.get("plan") or []
    findings = state.get("research_findings") or []
    completed_tasks = state.get("completed_tasks") or []
    
    new_plan = list(plan) # Copy plan to safely modify
    
    for task in plan:
        task_id = task.get("id")
        
        # We only evaluate tasks that the Scout marked as 'completed' (i.e. it attempted them)
        if task_id not in completed_tasks:
            continue
            
        # Check if we already evaluated this task (we can add a 'passed' flag to the finding)
        task_finding = next((f for f in findings if f.get("task_id") == task_id), None)
        if not task_finding or task_finding.get("evaluated", False):
            continue
            
        description = task.get("description")
        data = task_finding.get("scraped_data") or task_finding.get("data")
        
        # Yield log before LLM call
        yield {"logs": [f"Critic: Handing off to LLM to evaluate task '{task_id}'..."]}

        prompt = f"""
You are the Critic in an Autonomous Research Studio.
Your job is to objectively evaluate if the gathered data is sufficient to satisfy the research task.

Task Description: "{description}"
Gathered Data (snippet):
{data[:3000]}

Evaluation Criteria:
1. Does the data contain specific facts, figures, or answers requested in the task?
2. Is the source credible?
3. If the data is mostly navigation links or generic errors, set "pass" to false.

Respond ONLY with a valid JSON object:
{{
    "pass": true or false,
    "reason": "Detailed explanation of why it passed or failed",
    "follow_up_query": "If pass is false, provide a highly specific Google search query to find the missing data. If true, set to null."
}}
"""
        messages = [
            {"role": "system", "content": "You output only strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = query_llm(messages)
            eval_result = parse_json_robustly(response)
            
            task_finding["evaluated"] = True
            task_finding["pass"] = eval_result.get("pass", True)
            task_finding["reason"] = eval_result.get("reason", "No reason provided.")
            
            status = "PASSED" if task_finding["pass"] else "FAILED"
            yield {"logs": [f"Critic: Task {task_id} {status}. Reason: {task_finding['reason']}"]}
            
            if not task_finding["pass"]:
                # The Critic rejected it. We must loop back.
                # Remove from completed so Scout picks it up again
                completed_tasks.remove(task_id)
                # Update the task description with the Crits's suggested follow up
                for p in new_plan:
                    if p["id"] == task_id:
                        p["description"] = eval_result.get("follow_up_query", description)
                        p["source"] = "auto" # Force general search on retry
                        
        except Exception as e:
            print(f"[Critic] Failed to evaluate {task_id}: {e}")
            task_finding["evaluated"] = True
            task_finding["pass"] = True # Default to pass if LLM fails formatting to prevent infinite loop
            task_finding["reason"] = f"Evaluation failed error: {str(e)}"
            yield {"logs": [f"Critic: Task {task_id} FAILED evaluation due to error."]}

    # We yield the final state updates for the graph
    yield {"plan": new_plan, "completed_tasks": completed_tasks, "research_findings": findings}
