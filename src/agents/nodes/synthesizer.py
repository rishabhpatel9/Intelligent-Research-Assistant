from src.llm_client import query_llm
from src.agents.state import AgentState

def synthesizer_node(state: AgentState) -> dict:
    # Compiles the final beautiful dossier.
    query = state.get("query")
    findings = state.get("research_findings", [])
    
    # We only want to synthesize findings that passed the critic
    passed_findings = [f for f in findings if f.get("pass", True)]
    
    context_blocks = []
    for idx, f in enumerate(passed_findings):
        src = f.get("source", "Unknown")
        data = f.get("scraped_data") or f.get("data", "No data")
        context_blocks.append(f"--- Fact {idx+1} [Source: {src}] ---\n{data[:1500]}\n")
        
    context = "\n".join(context_blocks)
    
    prompt = f"""
You are the Master Synthesizer for an Autonomous Research Studio.
The user's original brief is: "{query}"

Using ONLY the verified research context provided below, synthesize a comprehensive, highly-detailed, and beautiful Markdown report.
You must:
1. Include an Executive Summary.
2. Use headers, bullet points, and tables where appropriate to make data readable.
3. Cite your sources inline using the [Source: X] metadata provided.
4. If the context does not fully answer the brief, state what remains unknown.
5. Provide a "References" section at the VERY END of the report. This section must list all the unique sources used in your report. Format each reference as a Markdown list item. If a source is a URL, it MUST be formatted as a clickable Markdown link (e.g., [Title or URL](URL)).

Context:
{context}
"""
    messages = [
        {"role": "system", "content": "You are an expert report writer. You output beautiful markdown."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        final_report = query_llm(messages)
    except Exception as e:
        final_report = f"[Synthesis Error] {e}"
        
    return {"result": final_report}
