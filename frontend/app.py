import gradio as gr
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
if API_URL.endswith("/query"):
    API_URL = API_URL.replace("/query", "")
    
def get_empty_df():
    return []

def run_query(query: str, thread_id: str):
    if not query.strip():
        # Clear output
        return [], thread_id, "Please enter a query!"
        
    # Force a completely new execution thread whenever a new plan is requested
    # This prevents state corruption if the user clicks "Plan Research" mid-session.
    thread_id = ""
        
    try:
        response = requests.post(f"{API_URL}/query", json={"query": query, "thread_id": None})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "requires_approval":
                new_thread_id = data["thread_id"]
                plan = data.get("plan", [])
                
                # Format plan into dataframe rows
                df_data = [[t.get("id", f"task_{i}"), t.get("source", "auto"), t.get("description", "")] for i, t in enumerate(plan)]
                    
                return df_data, new_thread_id, "_Review the generated plan below._"
            else:
                return [], thread_id, data.get("result", "Completed without output.")
        else:
            return [], thread_id, f"Error {response.status_code}: Could not process the query."
    except Exception as e:
        return [], thread_id, f"An error occurred: {str(e)}"

def approve_plan(thread_id: str, plan_df):
    if not thread_id:
        return "Error: No active session to approve."
        
    try:
        # Convert dataframe back to plan dicts
        new_plan = []
        for row in plan_df:
            # Drop empty rows
            if row[0] and row[2]:
                source = str(row[1]).lower()
                if source not in ["auto", "wikipedia", "arxiv"]:
                    source = "auto" # Default fallback for invalid sources
                new_plan.append({"id": row[0], "source": source, "description": row[2]})
                
        yield "Executing Research Plan... This may take a minute as agents scrape and synthesize data..."
        
        response = requests.post(f"{API_URL}/approve", json={"thread_id": thread_id, "plan": new_plan})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":
                yield data.get("message", f"Unexpected Error: {data}")
            else:
                yield data.get("result", "Synthesis complete. (No result returned by Graph)")
        else:
            yield f"Error {response.status_code}: Could not approve."
    except Exception as e:
        yield f"An error occurred: {str(e)}"

def replan(query: str):
    # Pass an empty thread to force a new execution graph
    return run_query(query, "")

def clear_ui():
    return "", "_Results will appear here..._", "", []

custom_theme = gr.themes.Soft(primary_hue="slate", secondary_hue="gray", neutral_hue="slate")

custom_css = """
:root, .gradio-container, body {
  --radius-xl: 8px !important;
  --radius-lg: 8px !important;
  --radius-md: 8px !important;
  --radius-sm: 8px !important;
  --block-radius: 8px !important;
  --button-large-radius: 8px !important;
  --button-small-radius: 8px !important;
  --container-radius: 8px !important;
  --input-radius: 8px !important;
}
.research-container { max-width: 800px !important; margin: 0 auto !important; padding-top: 2rem !important; }
.output-markdown { padding: 10px 12px !important; min-height: 200px; border: none !important; box-shadow: none !important; margin: 0 !important; background: transparent !important; }
.btn-green:hover { background-image: none !important; background-color: #10b981 !important; border-color: #10b981 !important; color: white !important; }
.btn-red:hover { background-image: none !important; background-color: #ef4444 !important; border-color: #ef4444 !important; color: white !important; }
.btn-blue:hover { background-image: none !important; background-color: #3b82f6 !important; border-color: #3b82f6 !important; color: white !important; }
.title-header { margin-bottom: 0.5rem !important; padding-top: 1rem !important; }
.subtitle-text { margin-bottom: 1rem !important; }
.header-bar { background-color: var(--block-label-background-fill) !important; border-bottom: none !important; margin: 0 !important; padding: 0.35rem 0.5rem !important; border-top-left-radius: 8px !important; border-top-right-radius: 8px !important; border-bottom-left-radius: 0px !important; border-bottom-right-radius: 0px !important; }
.header-bar p { text-align: center !important; font-size: 1.1em !important; font-weight: 600 !important; margin: 0 !important; color: var(--body-text-color) !important; }
"""

with gr.Blocks(title="Autonomous Research Studio") as iface:
    session_thread = gr.State("")

    with gr.Column(elem_classes="research-container"):
        gr.Markdown(
            """
            <h1 style="text-align: center;">Autonomous Research Studio</h1>
            Welcome to the multi-agent research swarm. Submit a brief, review the Orchestrator's plan, and let the agents deep scrape and synthesize a final report.
            """
        )
        
        with gr.Group():
            gr.Markdown("Research Brief", elem_classes="header-bar")
            query_input = gr.Textbox(lines=3, placeholder="Enter your complex research brief here...", show_label=False)
            with gr.Row():
                submit_btn = gr.Button("Plan Research", variant="primary", scale=2, elem_classes="btn-green")
                clear_btn = gr.Button("Clear", variant="secondary", scale=1, elem_classes="btn-red")
                
        gr.Markdown("<p class='subtitle-text' style='text-align: center; margin-bottom: 0px; padding-top: 0.5rem;'><em>Review and edit the Orchestrator's plan. You can modify search queries or sources before hitting Execute. Kindly wait a few seconds after requesting a research plan for the first time while we wake up the LLM from its nap.</em></p>")
        with gr.Group() as approval_group:
            gr.Markdown("Research Plan", elem_classes="header-bar")
            plan_editor = gr.Dataframe(
                value=[["", "auto", ""]],
                headers=["Task ID", "Source (auto/wikipedia/arxiv)", "Description"],
                type="array",
                column_count=(3, "fixed"),
                column_widths=["10%", "33%", "57%"],
                interactive=True,
                wrap=True,
                show_label=False
            )
            with gr.Row():
                approve_btn = gr.Button("Approve & Execute Plan", variant="primary", elem_classes="btn-green")
                replan_btn = gr.Button("Regenerate Plan", variant="secondary", elem_classes="btn-blue")

        with gr.Group():
            gr.Markdown("Output", elem_classes="header-bar")
            output_display = gr.Markdown(value="_Results will appear here..._", elem_classes="output-markdown")
        
        # Event listeners
        submit_btn.click(
            fn=run_query,
            inputs=[query_input, session_thread],
            outputs=[plan_editor, session_thread, output_display]
        )
        
        replan_btn.click(
            fn=replan,
            inputs=[query_input],
            outputs=[plan_editor, session_thread, output_display]
        )
        
        approve_btn.click(
            fn=approve_plan,
            inputs=[session_thread, plan_editor],
            outputs=[output_display]
        )
        
        clear_btn.click(
            fn=clear_ui,
            inputs=None,
            outputs=[query_input, output_display, session_thread, plan_editor]
        )

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", pwa=True, theme=custom_theme, css=custom_css)
