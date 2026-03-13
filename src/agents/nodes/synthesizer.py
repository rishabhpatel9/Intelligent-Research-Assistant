import re
from datetime import datetime
from src.llm_client import query_llm
from src.agents.state import AgentState

def synthesizer_node(state: AgentState) -> dict:
    # Create the final research report.
    query = state.get("query")
    findings = state.get("research_findings") or []
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Focus on findings that have been verified.
    passed_findings = [f for f in findings if f.get("pass", True)]
    
    context_blocks = []
    source_links = []
    
    for idx, f in enumerate(passed_findings):
        fact_num = idx + 1
        src = f.get("source", "Unknown")
        data = f.get("scraped_data") or f.get("data", "No data")
        
        # Identify source URLs for references.
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', data)
        primary_url = ""
        if urls:
            primary_url = urls[0]
            if primary_url.startswith("www."):
                primary_url = "https://" + primary_url
            source_links.append(f"Fact {fact_num}: {primary_url}")
        
        context_blocks.append(f"--- Fact {fact_num} [Source: {src}] ---\n{data[:2000]}\n")
        
    context = "\n".join(context_blocks)
    links_section = "\n".join(source_links) if source_links else "No URLs found."
    
    prompt = f"""
You are a Master Report Writer. You take snippets of verified research and transform them into a cohesive, high density academic style report. Avoid using unnecessary hyphens.
Today's Date: {current_date}
The user's query is: "{query}"

Using ONLY the verified research context provided below, synthesize a comprehensive, highly-detailed, and beautiful Markdown report.

### Structural Requirements:
1. **Header**: Start with a `# Research Report: [Topic]` title.
2. **Executive Summary**: A brief 3-4 sentence overview of findings.
3. **Formatting**: Use sub-headers (##), bullet points, and Bold text for emphasis. 
4. **Citations**: Use inline citations like `[Fact X]` where X corresponds to the Fact number.
5. **No Hallucinations**: Do not add information that is not present in the provided context.
6. **References Section**: At the end, provide a `### References` section.
   - For every Fact cited in the report, create a bulleted list item.
   - Format: `- [Description of the source](URL)`
   - **Crucial**: The part in brackets `[]` should be a short, descriptive title for the link. The part in parentheses `()` MUST be the exact URL provided in the "Source Link Map" below.
   - Example: If you cite `[Fact 1]`, the reference should be `- [Descriptive Title]({source_links[0].split(': ', 1)[1] if source_links else 'URL'})`
   - DO NOT use backticks. DO NOT use the words "Source Name/Title" literalized.

Source Link Map:
{links_section}

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
