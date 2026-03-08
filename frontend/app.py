import gradio as gr
import requests
import os

# Set local FastAPI backend URL base
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
# To handle backward compatibility if user passed /query in env
if API_URL.endswith("/query"):
    API_URL = API_URL.replace("/query", "")

def run_query(query: str, thread_id: str):
    if not query.strip():
        return "Please enter a query!", thread_id, gr.update(visible=False)
        
    try:
        response = requests.post(f"{API_URL}/query", json={"query": query, "thread_id": thread_id if thread_id else None})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "requires_approval":
                new_thread_id = data["thread_id"]
                plan = data.get("plan", [])
                
                plan_md = "## 📋 Research Plan Generated\n*Review the Orchestrator's plan before spending API credits.*\n\n"
                for i, t in enumerate(plan):
                    plan_md += f"{i+1}. **[{t.get('source', 'auto').upper()}]** {t.get('description')}\n"
                    
                return plan_md, new_thread_id, gr.update(visible=True)
            else:
                return data.get("result", "Completed without output."), thread_id, gr.update(visible=False)
        else:
            return f"Error {response.status_code}: Could not process the query.", thread_id, gr.update(visible=False)
    except Exception as e:
        return f"An error occurred: {str(e)}", thread_id, gr.update(visible=False)

def approve_plan(thread_id: str):
    if not thread_id:
        return "Error: No active session to approve.", gr.update(visible=False)
        
    try:
        yield "Executing Research Plan... This may take a minute as agents scrape and synthesize data...", gr.update(visible=False)
        response = requests.post(f"{API_URL}/approve", json={"thread_id": thread_id})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":
                yield data.get("message", f"Unexpected Error: {data}"), gr.update(visible=False)
            else:
                yield data.get("result", "Synthesis complete. (No result returned by Graph)"), gr.update(visible=False)
        else:
            yield f"Error {response.status_code}: Could not approve.", gr.update(visible=False)
    except Exception as e:
        yield f"An error occurred: {str(e)}", gr.update(visible=False)

def clear_ui():
    return "", "_Results will appear here..._", "", gr.update(visible=False)

# Theme
custom_theme = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="gray",
    neutral_hue="slate"
)

custom_css = """
.research-container { max-width: 800px !important; margin: 0 auto !important; padding-top: 2rem !important; }
.output-markdown { padding: 1.5rem; border-radius: 8px; background-color: var(--background-fill-secondary); border: 1px solid var(--border-color-primary); min-height: 200px; }
"""

with gr.Blocks(title="Autonomous Research Studio", theme=custom_theme, css=custom_css) as iface:
    # State variable to hold the LangGraph thread ID
    session_thread = gr.State("")

    with gr.Column(elem_classes="research-container"):
        gr.Markdown(
            """
            <h1 style="text-align: center;">Autonomous Research Studio</h1>
            
            Welcome to the multi-agent research swarm. Submit a brief, review the Orchestrator's plan, and let the agents deep-scrape and synthesize a final dossier.
            """
        )
        
        with gr.Group():
            query_input = gr.Textbox(
                lines=3,
                placeholder="Enter your complex research brief here...",
                label="Research Brief"
            )
            
            with gr.Row():
                submit_btn = gr.Button("1. Plan Research", variant="primary", scale=2)
                clear_btn = gr.Button("Clear", variant="secondary", scale=1)
                
        gr.Markdown("### Output")
        
        output_display = gr.Markdown(
            value="_Results will appear here..._", 
            elem_classes="output-markdown"
        )
        
        approve_btn = gr.Button("2. Approve & Execute Plan", variant="primary", visible=False)
        
        # Event listeners
        submit_btn.click(
            fn=run_query,
            inputs=[query_input, session_thread],
            outputs=[output_display, session_thread, approve_btn]
        )
        
        approve_btn.click(
            fn=approve_plan,
            inputs=[session_thread],
            outputs=[output_display, approve_btn]
        )
        
        clear_btn.click(
            fn=clear_ui,
            inputs=None,
            outputs=[query_input, output_display, session_thread, approve_btn]
        )

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", pwa=True)
