from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly
import re
from typing import Any, Dict

def critic_node(state: AgentState) -> dict:
    # Evaluates if the collected findings are sufficient for a given task.
    plan = state.get("plan") or []
    findings = state.get("research_findings") or []
    completed_tasks = state.get("completed_tasks") or []
    
    new_plan = list(plan) # Copy plan to safely modify
    
    MAX_RETRIES = 2

    for task in plan:
        task_id = task.get("id")
        
        # We only evaluate tasks that the Scout marked as 'completed' (i.e. it attempted them)
        if task_id not in completed_tasks:
            continue
            
        # Check if we already evaluated this task (we can add a 'passed' flag to the finding)
        task_finding = next((f for f in findings if f.get("task_id") == task_id), None)
        if not task_finding or task_finding.get("evaluated", False):
            continue
            
        description = str(task.get("description") or "")
        data = str((task_finding.get("scraped_data") or task_finding.get("data") or ""))
        attempts = int(task_finding.get("critic_attempts", 0))

        # If we've already tried a couple of times and still don't have
        # convincing data, stop looping and mark as best-effort.
        if attempts >= MAX_RETRIES:
            task_finding["evaluated"] = True
            task_finding["pass"] = True
            task_finding["reason"] = (
                "Marked sufficient after multiple review attempts with limited data."
            )
            continue

        desc = description.strip()
        is_simple = bool(
            re.match(r"^(what is|what are|define|explain|overview of|introduction to)\b", desc, re.I)
        )
        mode = "simple" if is_simple else "standard"
        
        prompt = f"""
You are the Critic node in a research pipeline. Your job is to judge if the data gathered by a scout is enough to answer a specific query.

### Context:
Task Description: "{description}"
Evaluation Mode: {mode}
Gathered Data (snippet):
{data[:3000]}

### Evaluation Rules:
1. **Strictness**: If the snippet contains mostly error messages (403 Forbidden, Cloudflare blocks) or is just a list of navigation links, you MUST fail it.
2. **Precision**: If the task asks for "2024 pricing" and the snippet only has "2023 pricing", you MUST fail it.
3. **Follow-up**: If you fail a task, you must provide a highly specific "follow_up_query" that targets the missing information.

### Response Format:
Output a single JSON object with these keys:
- "pass": (boolean) true if the data is sufficient.
- "reason": (string) concise explanation of your decision.
- "follow_up_query": (string or null) the targeted search query to fix the failure.

### Examples:
Task: "Find the current stock price of NVIDIA"
Data: "NVIDIA Corp (NVDA) is an American multinational technology company. It is known for its graphics processing units..."
{{{{
  "pass": false,
  "reason": "The snippet provides a general description of the company but does not contain a specific current stock price.",
  "follow_up_query": "NVIDIA (NVDA) current stock price real-time data"
}}}}
"""
        messages = [
            {"role": "system", "content": "You output only strictly valid JSON. No prose, no markdown wrappers."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = query_llm(messages)
            parsed = parse_json_robustly(response)
            eval_result: Dict[str, Any] = parsed if isinstance(parsed, dict) else {}
            
            task_finding["evaluated"] = True
            task_finding["pass"] = eval_result.get("pass", True)
            task_finding["reason"] = eval_result.get("reason", "No reason provided.")
            task_finding["critic_attempts"] = attempts + 1
            
            print(f"[Critic] Task {task_id} Eval: PASS={task_finding['pass']} | Reason: {task_finding['reason']}")
            
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

            
    node_logs = []
    for f in findings:
        if f.get("evaluated") and "pass" in f and not f.get("critic_logged"):
            status = "PASSED" if f["pass"] else "FAILED"
            node_logs.append(f"Critic: Task {f.get('task_id', 'unknown')} {status}. Reason: {f.get('reason', 'N/A')}")
            f["critic_logged"] = True

    return {"plan": new_plan, "logs": node_logs}
