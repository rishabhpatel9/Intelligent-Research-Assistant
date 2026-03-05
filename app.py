import gradio as gr
from src.agents.research_agent import workflow

def run_query(query: str):
    # Pass user query into the workflow and return result.
    result = workflow.invoke({"query": query})
    # Format output: show category + result
    return f"Category: {result['category']}\n\nResult:\n{result['result']}"

# Define Gradio interface
iface = gr.Interface(
    fn=run_query,
    inputs=gr.Textbox(lines=2, placeholder="Enter your query here..."),
    outputs="text",
    title="Intelligent Research Assistant",
    description="Ask questions, get search, summaries, fact-checks, or hybrid results."
)

if __name__ == "__main__":
    iface.launch()