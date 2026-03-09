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
        
        if not isinstance(plan, list):
            # Try to see if it's an object with a 'tasks' key or similar
            if isinstance(plan, dict):
                for key in ["tasks", "plan", "subtasks"]:
                    if key in plan and isinstance(plan[key], list):
                        plan = plan[key]
                        break
            if not isinstance(plan, list):
                plan = []
    except Exception as e:
        print(f"Failed to parse orchestrator JSON. Error: {e}\nRaw Response: {response}")
        plan = [{"id": "task_1", "description": query, "source": "auto"}]
        
    return {"plan": plan, "logs": [f"Orchestrator: Generated a {len(plan)}-task research plan."]}
