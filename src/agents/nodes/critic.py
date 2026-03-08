import json
from src.llm_client import query_llm
from src.agents.state import AgentState

def critic_node(state: AgentState) -> dict:
    # Evaluates if the collected findings are sufficient for a given task.
    plan = state.get("plan", [])
    findings = state.get("research_findings", [])
    completed_tasks = state.get("completed_tasks", [])
    
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
        
        prompt = f"""
You are the Critic in an Autonomous Research Studio.
Your job is to evaluate if the gathered data is sufficient to satisfy the research task.

Task Description: "{description}"
Gathered Data: "{data[:2000]}..."

Respond ONLY with a valid JSON object:
{{
    "pass": true or false,
    "reason": "short explanation",
    "follow_up_query": "If pass is false, provide a more specific Google search query to find the missing data. If true, set to null."
}}
"""
        messages = [
            {"role": "system", "content": "You output only strictly valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = query_llm(messages)
            cleaned = response.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            elif cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            
            eval_result = json.loads(cleaned.strip())
            
            task_finding["evaluated"] = True
            task_finding["pass"] = eval_result.get("pass", True)
            
            print(f"[Critic] Task {task_id} Eval: PASS={task_finding['pass']} | Reason: {eval_result.get('reason')}")
            
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
            
    return {"plan": new_plan} # Return updated plan (with modified queries if failed). completed_tasks was updated by reference but LangGraph handles it.
