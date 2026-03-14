from datetime import datetime
from src.llm_client import query_llm
from src.agents.state import AgentState
from src.utils.json_utils import parse_json_robustly

def orchestrator_node(state: AgentState) -> dict:
    """Decomposes the user's research brief into actionable sub-tasks."""
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
- **Entity Identification**: Use "wikipedia" for broad concepts or specific people/places.
- **Scientific Depth**: Use "arxiv" for technical, mathematical, or computer science queries.
- **Current Events**: Use "duckduckgo" for recent news or general web searches.
- **Temporal Precision**: For time sensitive queries, include the current year/date ({current_date[:10]}) directly in the task description to ensure fresh results.
- **Logical Flow**: Ensure tasks are sequential (e.g., define the concept before exploring its impacts).

### Example JSON:
User: "How does CRISPR-Cas9 work and what are its ethical implications?"
{{
  "tasks": [
    {{"id": "task_1", "description": "Mechanism of CRISPR-Cas9 gene editing technology", "source": "wikipedia"}},
    {{"id": "task_2", "description": "Key scientific breakthroughs in CRISPR 2024-2025", "source": "arxiv"}},
    {{"id": "task_3", "description": "Major ethical concerns and global regulations regarding germline gene editing", "source": "duckduckgo", "timelimit": "w"}}
  ]
}}
Return ONLY a valid JSON array. Ensure correct JSON syntax.
    """
    
    messages = [
        {"role": "system", "content": f"You are a JSON generator that outputs ONLY valid JSON objects. No prose, no markdown wrappers. Do not escape double quotes unless they are part of the text CONTENT itself. The Example JSON in user text is an example to show format, do not use the descripiton/content as output, come up with the questions based on the user query. Treat every request as a fresh task with no previous context. The current year is {current_date[:4]}. If the query is about news or real time data, ensure your search descriptions include the year/date to prevent outdated results."},
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