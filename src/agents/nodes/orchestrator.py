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
You are the Orchestration engine for an Autonomous Research Agent. Your goal is to take a user's research request and break it down into 3-5 distinct, targeted, and non-redundant search tasks.

[Seed: {salt}]
The user's research brief is: "{query}"

### Output Requirements:
1. **Format**: You MUST output a raw JSON array. 
2. **No Wrappers**: Do not include markdown code blocks (e.g., ```json).
3. **Task Structure**: Each object in the array must contain:
   - "id": A unique string identifier (e.g., "task_1").
   - "description": A specific, clear search query intended for a search engine.
   - "source": One of ["auto", "wikipedia", "arxiv", "duckduckgo"].

### Strategy:
- **Entity Identification**: Use "wikipedia" for broad concepts or specific people/places.
- **Scientific Depth**: Use "arxiv" for technical, mathematical, or computer science queries.
- **Current Events**: Use "duckduckgo" for recent news or general web searches.
- **Logical Flow**: Ensure tasks are sequential (e.g., define the concept before exploring its impacts).

### Examples:
User: "How does CRISPR-Cas9 work and what are its ethical implications?"
[
  {{"id": "task_1", "description": "Mechanism of CRISPR-Cas9 gene editing technology", "source": "wikipedia"}},
  {{"id": "task_2", "description": "Key scientific breakthroughs in CRISPR 2024-2025", "source": "arxiv"}},
  {{"id": "task_3", "description": "Major ethical concerns and global regulations regarding germline gene editing", "source": "duckduckgo"}}
]
    """
    
    messages = [
        {"role": "system", "content": "You are a JSON generator that outputs ONLY valid JSON arrays. No prose, no markdown wrappers."},
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
                    else:
                        # Sanitize ID: remove common hallucinated artifacts like escaped quotes or JSON keys
                        clean_id = str(task["id"]).replace('\\"', '').replace('"', '').replace('id:', '').strip()
                        task["id"] = clean_id or f"task_{i+1}"
                    
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
