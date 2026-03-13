from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly
import re
from typing import Any, Dict

def critic_node(state: AgentState) -> dict:
    # Assess if the collected data is enough to answer the research task.
    plan = state.get("plan") or []
    findings = state.get("research_findings") or []
    completed_tasks = state.get("completed_tasks") or []
    
    new_plan = list(plan)
    
    MAX_RETRIES = 2

    for task in plan:
        task_id = task.get("id")
        
        # Evaluate tasks completed by the search process.
        if task_id not in completed_tasks:
            continue
            
        # Skip if already evaluated.
        task_finding = next((f for f in findings if f.get("task_id") == task_id), None)
        if not task_finding or task_finding.get("evaluated", False):
            continue
            
        description = str(task.get("description") or "")
        data = str((task_finding.get("scraped_data") or task_finding.get("data") or ""))
        attempts = int(task_finding.get("critic_attempts", 0))

        # Stop reviewing after multiple attempts to avoid stalling.
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

Evaluation Criteria:
If Evaluation Mode is "simple" (definition/overview questions):
1. Pass if the snippet provides a clear, correct explanation/definition and basic context. Numbers/figures are NOT required.
2. If the snippet contains only generic errors, placeholders, or mostly navigation links, fail.
3. Prefer credible sources (Wikipedia, reputable orgs), but do not fail solely because the snippet is short.

If Evaluation Mode is "standard" (deeper research questions):
1. Pass only if the snippet contains specific, relevant details that directly answer the task (facts, mechanisms, comparisons, key points).
2. If the snippet is mostly navigation links or generic errors, fail.
3. Consider source credibility.

Respond ONLY with a valid JSON object:
{{
    "pass": true or false,
    "reason": "Detailed explanation of why it passed or failed",
    "follow_up_query": "If pass is false, provide a highly specific Google search query to find the missing data. If true, set to null."
}}
"""
        messages = [
            {"role": "system", "content": "You output only strictly valid JSON. No prose, no markdown wrappers."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = query_llm(messages, json_mode=True)
            parsed = parse_json_robustly(response)
            eval_result: Dict[str, Any] = parsed if isinstance(parsed, dict) else {}
            
            task_finding["evaluated"] = True
            task_finding["pass"] = eval_result.get("pass", True)
            task_finding["reason"] = eval_result.get("reason", "No reason provided.")
            task_finding["critic_attempts"] = attempts + 1
            
            print(f"[Critic] Task {task_id} Eval: PASS={task_finding['pass']} | Reason: {task_finding['reason']}")
            
            if not task_finding["pass"]:
                # Allow the search process to retry failed tasks.
                completed_tasks.remove(task_id)
                # Refine the query based on missing information.
                for p in new_plan:
                    if p["id"] == task_id:
                        p["description"] = eval_result.get("follow_up_query", description)
                        p["source"] = "auto"
                        
        except Exception as e:
            print(f"[Critic] Failed to evaluate {task_id}: {e}")
            task_finding["evaluated"] = True
            task_finding["pass"] = True # Pass by default on evaluation errors to avoid infinite loops.
            task_finding["reason"] = f"Evaluation failed error: {str(e)}"

            
    node_logs = []
    for f in findings:
        if f.get("evaluated") and "pass" in f and not f.get("critic_logged"):
            status = "PASSED" if f["pass"] else "FAILED"
            node_logs.append(f"Critic: Task {f.get('task_id', 'unknown')} {status}. Reason: {f.get('reason', 'N/A')}")
            f["critic_logged"] = True

    return {"plan": new_plan, "logs": node_logs}