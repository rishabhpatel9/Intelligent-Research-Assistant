
from src.agents.research_agent import classify_query_llm

queries = [
    "What are the latest AI techniques in healthcare?",
    "Summarize this article about climate change.",
    "Is it true that coffee causes dehydration?",
    "Compare renewable energy vs fossil fuels."
]

for q in queries:
    category = classify_query_llm(q)
    print(f"Query: {q}")
    print(f"LLM Classification: {category}\n")
