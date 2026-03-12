from src.llm_client import query_llm
from src.agents.state import AgentState

def synthesizer_node(state: AgentState) -> dict:
    # Compiles the final beautiful dossier.
    query = state.get("query")
    findings = state.get("research_findings") or []
    
    # We only want to synthesize findings that passed the critic
    passed_findings = [f for f in findings if f.get("pass", True)]
    
    context_blocks = []
    for idx, f in enumerate(passed_findings):
        src = f.get("source", "Unknown")
        data = f.get("scraped_data") or f.get("data", "No data")
        context_blocks.append(f"--- Fact {idx+1} [Source: {src}] ---\n{data[:1500]}\n")
        
    context = "\n".join(context_blocks)
    
    prompt = f"""
You are a Master Report Writer. You take snippets of verified research and transform them into a cohesive, high density academic style report. Avoid using unnecessary hyphens.
The user's query is: "{query}"
Using ONLY the verified research context provided below, synthesize a comprehensive, highly-detailed, and beautiful Markdown report.
You must follow the following structural requirements:
### Structural Requirements:
1. **Header**: Start with a `# Research Report: [Topic]` title.
2. **Executive Summary**: A brief 3-4 sentence overview of findings.
3. **Formatting**: Use sub-headers (##), bullet points, and Bold text for emphasis. 
4. **Citations**: Use inline citations like `[Source: X]` based on the metadata provided in the facts.
5. **No Hallucinations**: Do not add information that is not present in the provided context.
6. **Reference Table**: At the end, provide a `### References` section listing all sources as clickable markdown links.

Context:
{context}
"""
    messages = [
        {"role": "system", "content": "You are an expert report writer. You output beautiful markdown. No conversational filler."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        final_report = query_llm(messages)
    except Exception as e:
        final_report = f"[Synthesis Error] {e}"
        
    return {"result": final_report, "logs": ["Synthesizer drafted the research report using verified findings."]}