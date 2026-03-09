from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly

def orchestrator_node(state: AgentState) -> dict:
    """Decomposes the user's research brief into actionable sub-tasks."""
    query = state["query"]
    
    import random
    salt = random.randint(1000, 9999)
    # Adding a random salt instruction variation forces exactly deterministic local LLMs to re-sample
    # their token distribution, yielding a completely different alternative plan.
    
    prompt = f"""
[Seed: {salt}]
You are the Orchestrator for an Autonomous Research Studio.
The user's research brief is: "{query}"

Decompose this brief into a few (3-5) high-quality, focused, and actionable search tasks.
Focus on directly answering the user's question. Avoid redundant or overly broad queries.

Each task must have:
- "id": A unique string ID (e.g. "task_1")
- "description": The specific search query.
- "source": Choose from: ["auto", "wikipedia", "arxiv"]. Use wikipedia for entities, arxiv for science/CS, and auto for general web.

Return ONLY a valid JSON array. Ensure correct JSON syntax.
    """
    
    messages = [
        {"role": "system", "content": "You are a JSON generator that outputs ONLY valid JSON arrays. Do not escape double quotes unless they are part of the text CONTENT itself."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = query_llm(messages)
        plan = parse_json_robustly(response)
        
        # If the LLM returned a dictionary instead of a list, try to find the list inside it
        if isinstance(plan, dict):
            for key in ["tasks", "plan", "subtasks", "research_tasks"]:
                if key in plan and isinstance(plan[key], list):
                    plan = plan[key]
                    break
        
        # Validate that plan is a list of tasks
        if not isinstance(plan, list) or not plan:
            print(f"Orchestrator returned empty or invalid plan format: {plan}")
            plan = []
            
        # Ensure each item in the plan is a dictionary with at least 'description'
        if plan:
            validated_plan = []
            for i, task in enumerate(plan):
                if isinstance(task, dict) and task.get("description"):
                    # Fill in missing fields if necessary
                    if not task.get("id"):
                        task["id"] = f"task_{i+1}"
                    if not task.get("source"):
                        task["source"] = "auto"
                    validated_plan.append(task)
            plan = validated_plan

    except Exception as e:
        print(f"Failed to parse orchestrator JSON. Error: {e}\nRaw Response: {response}")
        plan = []

    # Final fallback: if no valid tasks were generated, use the original query as a single task
    status_msg = f"Orchestrator: Generated a {len(plan)}-task research plan."
    if not plan:
        plan = [{"id": "task_1", "description": query, "source": "auto"}]
        status_msg = "Orchestrator: LLM failed to generate a structured plan. Falling back to simple research mode."
        
    return {"plan": plan, "logs": [status_msg]}
