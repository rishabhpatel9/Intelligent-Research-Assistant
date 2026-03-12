import re
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
        
        # Extract URLs from findings to ensure they aren't lost in truncation
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', data)
        # Use first URL as the primary one for the header
        url_text = f" | URL: {urls[0]}" if urls else ""
        
        context_blocks.append(f"--- Fact {idx+1} [Source: {src}{url_text}] ---\n{data[:2000]}\n")
        
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
4. **Citations**: Use inline citations like `[Fact X]` where X corresponds to the Fact number in the context below.
5. **No Hallucinations**: Do not add information that is not present in the provided context.
6. **References Section**: At the end, provide a `### References` section. List all unique sources as a bulleted list (using `- `). Each reference MUST include a clickable markdown link to the URL provided in the context. Ensure each reference is on its own separate line.

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