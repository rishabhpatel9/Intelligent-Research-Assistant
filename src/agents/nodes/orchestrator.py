import json
from src.llm_client import query_llm
from src.agents.state import AgentState

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
The user has provided the following research brief:
"{query}"

Your job is to decompose this brief into a list of highly creative, specific, and actionable search tasks.
Explore diverse angles and deep nuances of the topic.
Each task must have:
- "id": A unique string ID (e.g. "task_1")
- "description": The specific search query or data to find.
- "source": The preferred search source. Choose from: ["auto", "wikipedia", "arxiv"]. Use wikipedia for entities/history, arxiv for scientific/CS papers, and auto for general web.

Respond ONLY with a valid JSON array of these task objects. Do not include markdown formatting or other text.
    """
    
    messages = [
        {"role": "system", "content": "You output only strictly valid JSON arrays. Never output anything else."},
        {"role": "user", "content": prompt}
    ]
    
    response = query_llm(messages)
    
    try:
        cleaned = response.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"): cleaned = cleaned[3:]
        if cleaned.endswith("```"): cleaned = cleaned[:-3]
            
        plan = json.loads(cleaned.strip())
        if not isinstance(plan, list):
            plan = []
    except Exception as e:
        print(f"Failed to parse orchestrator JSON. Error: {e}\nRaw Response: {response}")
        # Fallback single-step plan
        plan = [{"id": "task_1", "description": query, "source": "auto"}]
        
    return {"plan": plan}
