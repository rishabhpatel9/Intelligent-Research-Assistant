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
        return [], thread_id, "Please enter a query!", []

    # Force a completely new execution thread whenever a new plan is requested
    thread_id = ""

    try:
        response = requests.post(f"{API_URL}/query", json={"query": query, "thread_id": None})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "requires_approval":
                new_thread_id = data["thread_id"]
                plan = data.get("plan", [])
                initial_logs = data.get("logs", [])
                
                # Format plan into dataframe rows
                df_data = [[t.get("id", f"task_{i}"), t.get("source", "auto"), t.get("description", "")] for i, t in enumerate(plan)]

                # Convert logs to Visibly Thinking format
                # We use a single assistant message with a title for Orchestration
                messages = [
                    {
                        "role": "assistant", 
                        "content": "\n".join(initial_logs) if initial_logs else "Orchestrator has analyzed the brief.",
                        "metadata": {"title": "Orchestrator: Planning", "status": "done"}
                    }
                ]
                
                return df_data, new_thread_id, "_Review the generated plan below._", messages
            else:
                return [], thread_id, data.get("result", "Completed without output."), []
        else:
            return [], thread_id, f"Error {response.status_code}: Could not process the query.", []
    except Exception as e:
        return [], thread_id, f"An error occurred: {str(e)}", []

import json

def approve_plan(thread_id: str, plan_df, current_messages):
    """Approve the plan and stream log messages from the backend.
    Yields (final_result, messages, helper_html) for Gradio to update components.
    The helper_html field is used for small client-side helpers (e.g. scrolling).
    """
    if not thread_id:
        yield "", current_messages, ""
        return

    # Use existing messages from Orchestrator
    messages = list(current_messages) if current_messages else []
    current_step_title = None
 
    yield "_Research in progress... Results will appear here shortly._", messages, ""

    try:
        new_plan = []
        for row in plan_df:
            if row and len(row) >= 3:
                task_id = row[0]
                source = str(row[1] if row[1] is not None else "auto").lower()
                description = row[2]
                if task_id and description:
                    if source not in ["auto", "wikipedia", "arxiv"]:
                        source = "auto"
                    new_plan.append({"id": task_id, "source": source, "description": description})

        # Use requests with stream=True to consume the backend's EventStream
        with requests.post(f"{API_URL}/approve", json={"thread_id": thread_id, "plan": new_plan}, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            try:
                                data = json.loads(decoded_line[6:])
                                event = data.get("event")
                                
                                if event == "step_start":
                                    # Mark previous assistant messages as done before starting a new step
                                    for m in messages:
                                        if m.get("role") == "assistant" and m.get("metadata", {}).get("status") == "pending":
                                            m["metadata"]["status"] = "done"

                                    # Remember the current step title; individual logs will
                                    # carry this in their metadata so we don't need an
                                    # empty placeholder message.
                                    current_step_title = data.get("message", "Agent processing...")
                                    yield "_Synthesis in progress... Listening to agents..._", messages, ""
                                
                                elif event == "step_log":
                                    # Append each log entry as its own message with the
                                    # appropriate step title so the Thinking Log remains
                                    # readable and avoids an initial empty entry.
                                    log_entry = data.get("log", "")
                                    step_title = current_step_title or "Agent processing..."
                                    messages.append({
                                        "role": "assistant",
                                        "content": f"{log_entry}",
                                        "metadata": {"title": step_title, "status": "pending"}
                                    })
                                    yield "_Synthesis in progress... Listening to agents..._", messages, ""
                                        
                                elif data.get("status") == "completed":
                                    # Mark all assistant messages as done once the run completes
                                    for m in messages:
                                        if m.get("role") == "assistant":
                                            m.setdefault("metadata", {})
                                            m["metadata"]["status"] = "done"
                                    
                                    final_res = data.get("result", "")
                                    # No special scrolling to the output section; just return the result.
                                    yield final_res, messages, ""
                                    
                                elif data.get("status") == "error":
                                    err_msg = data.get("message", "Unknown error")
                                    messages.append({"role": "assistant", "content": f"Error: {err_msg}", "metadata": {"title": "System Error"}})
                                    yield f"An error occurred: {err_msg}", messages, ""
                            except json.JSONDecodeError:
                                continue
            else:
                messages.append({"role": "assistant", "content": f"Connection Error: Status {response.status_code}", "metadata": {"title": "Connection Error"}})
                yield f"Error {response.status_code}: Could not connect to backend.", messages, ""
    except Exception as e:
        messages.append({"role": "assistant", "content": str(e), "metadata": {"title": "Exception"}})
        yield f"An error occurred: {str(e)}", messages, ""

def replan(query: str):
    # Pass an empty thread to force a new execution graph
    return run_query(query, "")

def clear_ui(current_thread_id: str):
    # Signal the backend to cancel any in-flight run for this thread.
    if current_thread_id:
        try:
            requests.post(f"{API_URL}/cancel", json={"thread_id": current_thread_id}, timeout=3)
        except Exception:
            # Best-effort cancel; UI should still clear even if this fails.
            pass
    return "", "_Results will appear here..._", "", [], []

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
.research-container { max-width: 1000px !important; margin: 0 auto !important; padding-top: 2rem !important; }
.output-markdown { padding: 10px 12px !important; min-height: 200px; border: none !important; box-shadow: none !important; margin: 0 !important; background: transparent !important; }
.btn-green:hover { background-image: none !important; background-color: #10b981 !important; border-color: #10b981 !important; color: white !important; }
.btn-red:hover { background-image: none !important; background-color: #ef4444 !important; border-color: #ef4444 !important; color: white !important; }
.btn-blue:hover { background-image: none !important; background-color: #3b82f6 !important; border-color: #3b82f6 !important; color: white !important; }
.title-header { margin-bottom: 0.5rem !important; padding-top: 1rem !important; }
.subtitle-text { margin-bottom: 1rem !important; }
.header-bar { background-color: var(--block-label-background-fill) !important; border-bottom: none !important; margin: 0 !important; padding: 0.35rem 0.5rem !important; border-top-left-radius: 8px !important; border-top-right-radius: 8px !important; border-bottom-left-radius: 0px !important; border-bottom-right-radius: 0px !important; }
.header-bar p { text-align: center !important; font-size: 1.1em !important; font-weight: 600 !important; margin: 0 !important; color: var(--body-text-color) !important; }
.log-sidebar { border: none !important; box-shadow: none !important; margin: 0 !important; background: transparent !important; }
.log-sidebar .message-wrap { background: transparent !important; }
.log-sidebar .message-row { padding: 0 !important; }
.log-sidebar .avatar-container { display: none !important; }
"""


with gr.Blocks(title="Autonomous Research Studio") as iface:
    session_thread = gr.State("")
    with gr.Column(elem_classes="research-container"):
        gr.Markdown("""
        <h1 style="text-align: center;">Autonomous Research Studio</h1>
        Welcome to the multi-agent research swarm. Submit a brief, review the Orchestrator's plan, and let the agents deep scrape and synthesize a final report.
        """)
        
        with gr.Group():
            gr.Markdown("Research Brief", elem_classes="header-bar")
            query_input = gr.Textbox(lines=3, placeholder="Enter your complex research brief here...", show_label=False)
            with gr.Row():
                submit_btn = gr.Button("Plan Research", variant="primary", scale=2, elem_classes="btn-green")
                clear_btn = gr.Button("Clear", variant="secondary", scale=1, elem_classes="btn-red")
            
        gr.Markdown("<p class='subtitle-text' style='text-align: center; margin-bottom: 0px; padding-top: 0.5rem;'><em>Review and edit the Orchestrator's plan. You can modify search queries or sources before hitting Execute. Kindly wait a few seconds after requesting a research plan for the first time while we wake up the LLM from its nap.</em></p>")
        
        # Row containing Research Plan and Thinking Log
        with gr.Row():
            with gr.Column(scale=7):
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
            with gr.Column(scale=3):
                with gr.Group():
                    gr.Markdown("Thinking Log", elem_classes="header-bar")
                    log_output = gr.Chatbot(
                        label="Thinking Process", 
                        show_label=False, 
                        autoscroll=True, 
                        height=450, 
                        max_height=450,
                        layout="panel",
                        buttons=["copy_all"],
                        elem_classes="log-sidebar"
                    )

        with gr.Group():
            gr.Markdown("Output", elem_classes="header-bar")
            output_display = gr.Markdown(value="_Results will appear here..._", elem_classes="output-markdown")
            scroll_helper = gr.HTML(visible=False, sanitize=False)
    # Event listeners
    submit_btn.click(
        fn=run_query,
        inputs=[query_input, session_thread],
        outputs=[plan_editor, session_thread, output_display, log_output],
        scroll_to_output=True
    )
    replan_btn.click(
        fn=replan,
        inputs=[query_input],
        outputs=[plan_editor, session_thread, output_display, log_output],
        scroll_to_output=True
    )
    approve_btn.click(
        fn=approve_plan,
        inputs=[session_thread, plan_editor, log_output],
        outputs=[output_display, log_output, scroll_helper],
        scroll_to_output=True
    )
    clear_btn.click(
        fn=clear_ui,
        inputs=[session_thread],
        outputs=[query_input, output_display, session_thread, plan_editor, log_output]
    )

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", pwa=True, theme=custom_theme, css=custom_css)
