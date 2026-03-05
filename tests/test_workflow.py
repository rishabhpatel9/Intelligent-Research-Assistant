from src.agents.research_agent import workflow

queries = [
    "What are the latest AI techniques in healthcare?",
    "Summarize this article about climate change.",
    "Is it true that coffee causes dehydration?",
    "Compare renewable energy vs fossil fuels."
]

for q in queries:
    result = workflow.invoke({"query": q})
    print(f"Query: {q}")
    print(f"Category: {result['category']}")
    print(f"Result: {result['result']}\n")