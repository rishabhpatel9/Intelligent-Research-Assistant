from datetime import datetime
from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly

def orchestrator_node(state: AgentState) -> dict:
    # Decomposes the user's research brief into actionable sub-tasks.
    query = state["query"]
    
    import random
    salt = random.randint(1000, 9999)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
[Today's Date: {current_date}]
[Seed: {salt}]
You are the Orchestration node for an Autonomous Research Agent. Your goal is to take a user's research request and break it down into 1-5 distinct, targeted, and non-redundant search tasks to thoroughly answer the user's query.
The user's research brief is: "{query}"

Decompose this brief into a few (1-5) high-quality, focused, and actionable search tasks.
Focus on directly answering the user's question. Avoid redundant or overly broad queries.

### Output Requirements:
1. **Format**: You MUST output a valid JSON object. 
2. **Key**: Wrap the list of tasks in a key called "tasks".
3. **No Wrappers**: Do not include markdown code blocks (e.g., ```json).
4. **Task Structure**: Each object in the "tasks" array must contain:
   - "id": A unique string identifier (e.g., "task_1").
   - "description": A specific, clear search query intended for a search engine.
   - "source": One of ["auto", "wikipedia", "arxiv", "duckduckgo"].
   - "timelimit": (Optional) Use "d" for day, "w" for week, "m" for month, or "y" for year.

### Strategy:
1. **Wikipedia/Concepts**: Use for broad, foundational concepts.
2. **Arxiv/Scientific**: Use for technical depth.
3. **DuckDuckGo/General**: Use for recent news/web.
4. **Conditional Temporal Precision**: 
   - ONLY include specific dates (e.g. {current_date[:10]}) or the year (e.g. {current_date[:4]}) if the user's brief mentions time-sensitive keywords: "latest", "2026", "today", "current", "updated", "recent breakthroughs".
   - DO NOT append the year for general questions (like 'What is X?').

### Output Requirements:
1. **Format**: Valid JSON object. 
2. **Key**: Wrap tasks in a key called "tasks".
3. **Task Structure**: {{"id": "...", "description": "...", "source": "...", "timelimit": "..."}}

Return ONLY the JSON. No prose.
    """
    
    messages = [
        {"role": "system", "content": f"You are a JSON generator. Treat every request as a fresh task. The current year is {current_date[:4]}. ONLY include the year in search descriptions if the user query is clearly about news, recent events, or real-time data. For general/foundational questions, keep the search query timeless."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        response = query_llm(messages, json_mode=True)
        plan = parse_json_robustly(response)
        
        # Extract task list from response dictionary.
        if isinstance(plan, dict):
            for key in ["tasks", "plan", "subtasks", "research_tasks"]:
                if key in plan and isinstance(plan[key], list):
                    plan = plan[key]
                    break
        
        # Ensure the plan contains actionable tasks.
        if not isinstance(plan, list) or not plan:
            print(f"Orchestrator returned empty or invalid plan format: {plan}")
            plan = []
            
        # Validate each task contains a valid description.
        if plan:
            validated_plan = []
            for i, task in enumerate(plan):
                if isinstance(task, dict) and task.get("description"):
                    # Set default values for missing task fields.
                    if not task.get("id"):
                        task["id"] = f"task_{i+1}"
                    else:
                        # Clean up task ID to remove formatting artifacts.
                        clean_id = str(task["id"]).replace('\\"', '').replace('"', '').replace('id:', '').strip()
                        task["id"] = clean_id or f"task_{i+1}"
                    
                    if not task.get("source"):
                        task["source"] = "auto"
                    if not task.get("timelimit"):
                        task["timelimit"] = None
                    validated_plan.append(task)
            plan = validated_plan

    except Exception as e:
        print(f"Failed to parse orchestrator JSON. Error: {e}\nRaw Response: {response}")
        plan = []

    # Default to a single research task if no structured plan is available.
    status_msg = f"Generated a {len(plan)} task research plan."
    if not plan:
        plan = [{"id": "task_1", "description": query, "source": "auto"}]
        status_msg = "LLM failed to generate a structured plan. Falling back to simple research mode."
        
    return {"plan": plan, "logs": [status_msg]}