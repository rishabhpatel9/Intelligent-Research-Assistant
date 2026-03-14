import os
import json
from datetime import datetime
from src.agents.research_agent import workflow

FAILURE_QUERIES = [
    "What are the top 3 trending topics on X (Twitter) in the last 2 hours in India",
    "Compare the stock price of NVIDIA today at market open vs yesterday's close.",
    "Summarize the 'Risk Factors' section of the latest 10-K filing (PDF) for Tesla.",
    "Find the exact revenue figures for OpenAI in 2023 from 3 different sources and highlight any discrepancies.",
    "Who is the CEO of the company that recently acquired legora, and what is their personal background in AI?",
    "Find the Python documentation for the latest release of the polars library and explain how to use the new LazyFrame feature.",
    "What is the current public sentiment in France regarding the latest pension reform, based on French news outlets?",
    "Explain the mathematical proof behind the 'Attention is All You Need' paper and list the specific hardware used for training.",
    "Research the current open job positions at Amazon India (Bangalore) listed on their official careers portal.",
    "Give me a report on the 'Jaguar' population.",
    "What is the result of todays f1 qualifying and who was first and last?"
]

def run_regression():
    report_file = "regression_reports.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Regression Testing Report\n\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    for idx, query in enumerate(FAILURE_QUERIES):
        print(f"[{idx+1}/{len(FAILURE_QUERIES)}] Running query: {query}")
        thread_id = f"test_thread_{idx+1}_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}
        
        # 1. Initial invocation (Orchestrator)
        initial_state = {
            "query": query,
            "category": "",
            "plan": [],
            "research_findings": [],
            "completed_tasks": [],
            "messages": [],
            "logs": []
        }
        
        try:
            # First pass: Orchestrator to Review Plan
            workflow.invoke(initial_state, config=config)
            state = workflow.get_state(config)
            
            plan = state.values.get("plan", [])
            print(f"   Plan generated: {len(plan)} tasks")
            
            # 2. Approve and Execute (Scout -> Reader -> Critic -> Synthesizer)
            # Since we interrupted at review_plan, we resume
            workflow.invoke(None, config=config)
            
            final_state = workflow.get_state(config)
            result = final_state.values.get("result", "NO RESULT GENERATED")
            logs = final_state.values.get("logs", [])
            
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"## Query {idx+1}: {query}\n\n")
                f.write("### Plan\n")
                f.write(json.dumps(plan, indent=2) + "\n\n")
                f.write("### Results\n")
                f.write(result + "\n\n")
                f.write("### Logs\n")
                f.write("- " + "\n- ".join(logs) + "\n\n")
                f.write("---\n\n")
                
            print(f"   Done.")
            
        except Exception as e:
            print(f"   Error running query {idx+1}: {e}")
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"## Query {idx+1}: {query}\n\n")
                f.write(f"**ERROR**: {str(e)}\n\n")
                f.write("---\n\n")

if __name__ == "__main__":
    run_regression()
