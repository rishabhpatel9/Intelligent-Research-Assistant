import gradio as gr
import requests
import os
import random

def generate_challenge():
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    return f"**Solve this to access the studio:** {a} + {b} = ?", a + b

def verify_human(answer, target):
    try:
        if answer and int(answer) == int(target):
            return gr.update(visible=False), gr.update(visible=True), True, gr.update(visible=False), target, "", gr.update()
    except Exception:
        pass
    new_q, new_a = generate_challenge()
    return gr.update(), gr.update(), False, gr.update(visible=True, value="<p style='color: #ef4444; font-weight: 600;'>Verification failed. Please try again.</p>"), new_a, "", new_q


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
if API_URL.endswith("/query"):
    API_URL = API_URL.replace("/query", "")

def get_empty_df():
    return []

def run_query(query: str, thread_id: str):
    if not query.strip():
        return [gr.update(visible=False) for _ in range(8*4)] + [thread_id, "Please enter a query!", []]

    # Reset the execution thread for a new research request.
    thread_id = ""

    try:
        response = requests.post(f"{API_URL}/query", json={"query": query, "thread_id": None})
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "requires_approval":
                new_thread_id = data["thread_id"]
                plan = data.get("plan", [])
                initial_logs = data.get("logs", [])
                
                updates = []
                for i in range(8):
                    if i < len(plan):
                        task = plan[i]
                        updates.extend([
                            gr.update(visible=True),
                            gr.update(value=task.get("id", f"task_{i+1}"), visible=True),
                            gr.update(value=task.get("source", "auto"), visible=True),
                            gr.update(value=task.get("description", ""), visible=True)
                        ])
                    else:
                        # Explicitly clear values and hide
                        updates.extend([
                            gr.update(visible=False),
                            gr.update(value="", visible=False), 
                            gr.update(value="auto", visible=False),
                            gr.update(value="", visible=False)
                        ])

                messages = [
                    {
                        "role": "assistant", 
                        "content": "Orchestrator is analyzing the brief and generating a research plan...",
                        "metadata": {"title": "Orchestrator is planning", "status": "pending"}
                    }
                ]
                
                # Mark planning as complete if logs are available.
                messages[0]["metadata"]["status"] = "done"
                if initial_logs:
                    messages.append({
                        "role": "assistant",
                        "content": "\n".join(initial_logs),
                        "metadata": {"title": "Research plan created", "status": "done"}
                    })
                else:
                    # Mark the first message as done if no detailed logs are available.
                    messages[0]["metadata"]["title"] = "Research plan created"
                    messages[0]["content"] = "Orchestrator has analyzed the brief."

                return updates + [new_thread_id, "_Review the generated plan below._", messages]
            else:
                return [gr.update(visible=False) for _ in range(8*4)] + [thread_id, data.get("result", "Completed without output."), []]
        else:
            return [gr.update(visible=False) for _ in range(8*4)] + [thread_id, f"Error {response.status_code}: Could not process the query.", []]
    except Exception as e:
        return [gr.update(visible=False) for _ in range(8*4)] + [thread_id, f"An error occurred: {str(e)}", []]

import json

def approve_plan(thread_id: str, current_messages, *task_inputs):
    #Confirm the plan and stream progress updates from the server.
    if not thread_id:
        yield "", current_messages, ""
        return

    messages = list(current_messages) if current_messages else []
    current_step_title = None
 
    yield "_Research in progress... Results will appear here shortly._", messages, ""

    try:
        new_plan = []
        for i in range(0, 24, 3):
            task_id = task_inputs[i]
            source = str(task_inputs[i+1] if task_inputs[i+1] is not None else "auto").lower()
            description = task_inputs[i+2]
            
            if task_id and description:
                if source not in ["auto", "duckduckgo", "wikipedia", "arxiv"]:
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
                                    # Finalize previous status updates.
                                    for m in messages:
                                        if m.get("role") == "assistant" and m.get("metadata", {}).get("status") == "pending":
                                            m["metadata"]["status"] = "done"

                                    current_step_title = data.get("message", "Agent processing...")
                                    yield "_Synthesis in progress... Listening to agents..._", messages, ""
                                
                                elif event == "step_log":
                                    log_entry = data.get("log", "")
                                    step_title = current_step_title or "Agent processing..."
                                    messages.append({
                                        "role": "assistant",
                                        "content": f"{log_entry}",
                                        "metadata": {"title": step_title, "status": "pending"}
                                    })
                                    yield "_Synthesis in progress... Listening to agents..._", messages, ""
                                        
                                elif data.get("status") == "completed":
                                     # Finalize status updates on completion.
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
    return run_query(query, "")

def clear_ui(current_thread_id: str):
    # Cancel any active research for the current thread.
    if current_thread_id:
        try:
            requests.post(f"{API_URL}/cancel", json={"thread_id": current_thread_id}, timeout=3)
        except Exception:
            pass
    return ["", "_Results will appear here..._", ""] + [gr.update(visible=False) for _ in range(8*4)] + [[]]

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
.title-header { margin-bottom: 0.5rem !important; padding-top: 1rem !important; text-align: center !important; }
.subtitle-text { margin-bottom: 1rem !important; }
.header-bar { background-color: var(--block-label-background-fill) !important; border-bottom: none !important; margin: 0 !important; padding: 0.35rem 0.5rem !important; border-top-left-radius: 8px !important; border-top-right-radius: 8px !important; border-bottom-left-radius: 0px !important; border-bottom-right-radius: 0px !important; }
.header-bar p { text-align: center !important; font-size: 1.1em !important; font-weight: 600 !important; margin: 0 !important; color: var(--body-text-color) !important; }
.log-sidebar { border: none !important; box-shadow: none !important; margin: 0 !important; background: transparent !important; }
.log-sidebar .message-wrap { background: transparent !important; }
.log-sidebar .message-row { padding: 0 !important; }
.log-sidebar .avatar-container { display: none !important; }
.verification-card { max-width: 500px !important; margin: 100px auto !important; padding: 2rem !important; background: var(--block-background-fill) !important; border-radius: 12px !important; border: 1px solid var(--border-color-primary) !important; box-shadow: var(--shadow-drop-lg) !important; }
.challenge-box { font-size: 1.2rem !important; font-weight: 600 !important; margin: 1rem 0 !important; border: 1px dashed var(--border-color-primary) !important; padding: 1rem !important; border-radius: 8px !important; background: var(--background-fill-secondary) !important; text-align: center !important; }
.task-header { padding: 5px 10px !important; border-bottom: 1px solid var(--border-color-primary) !important; margin-bottom: 5px !important; }
.task-header p { margin: 0 !important; font-size: 0.9em !important; color: var(--body-text-color-subdued) !important; }
.copy-btn { width: auto !important; height: 30px !important; min-width: 120px !important; padding: 0 10px !important; font-size: 0.85em !important; background: var(--block-label-background-fill) !important; border: 1px solid var(--border-color-primary) !important; }
.copy-btn:hover { background: var(--background-fill-secondary) !important; color: var(--primary-500) !important; }
"""


with gr.Blocks(title="Autonomous Research Studio") as iface:
    session_thread = gr.State("")
    is_verified = gr.State(False)
    target_answer = gr.State(0)

    with gr.Column(visible=True, elem_classes="verification-card") as gate_ui:
        gr.Markdown("## Beep boop, are you a bot?", elem_classes="title-header")
        gr.Markdown("Please solve this simple challenge to access the Autonomous Research Studio to help prevent spam and server overload.")
        challenge_display = gr.Markdown("", elem_classes="challenge-box")
        user_answer = gr.Textbox(placeholder="Enter the result here...", show_label=False, container=False)
        verify_btn = gr.Button("Verify & Enter Studio", variant="primary", elem_classes="btn-green")
        error_msg = gr.Markdown(visible=False)

    with gr.Column(visible=False, elem_classes="research-container") as main_ui:
        gr.Markdown("""
        <h1 style="text-align: center;">Autonomous Research Studio</h1>
        Welcome to the multi-agent research swarm. Submit a brief, review the Orchestrator's plan, and let the agents deep scrape and synthesize a final report.
        """)
        
        with gr.Group():
            gr.Markdown("Research Brief", elem_classes="header-bar")
            query_input = gr.Textbox(placeholder="Enter your complex research brief here...", show_label=False)
            with gr.Row():
                submit_btn = gr.Button("Plan Research", variant="primary", scale=2, elem_classes="btn-green")
                clear_btn = gr.Button("Clear", variant="secondary", scale=1, elem_classes="btn-red")
            
        gr.Markdown("<p class='subtitle-text' style='text-align: center; margin-bottom: 0px; padding-top: 0.5rem;'><em>Review and edit the Orchestrator's plan. You can modify search queries or sources before hitting Execute. Kindly wait a few seconds after requesting a research plan for the first time while we wake up the LLM from its nap.</em></p>")
        
        # Row containing Research Plan and Thinking Log
        with gr.Row():
            with gr.Column(scale=7):
                with gr.Group() as approval_group:
                    gr.Markdown("Research Plan", elem_classes="header-bar")
                    with gr.Row(elem_classes="task-header"):
                        with gr.Column(scale=1, min_width=0):
                            gr.Markdown("**Task ID**")
                        with gr.Column(scale=2, min_width=0):
                            gr.Markdown("**Source**")
                        with gr.Column(scale=6, min_width=0):
                            gr.Markdown("**Description**")
                    task_components = []
                    for i in range(8):
                        with gr.Row(visible=False) as row:
                            with gr.Column(scale=1, min_width=0):
                                tid = gr.Textbox(interactive=False, container=False, show_label=False)
                            with gr.Column(scale=2, min_width=0):
                                tsrc = gr.Dropdown(
                                    choices=["auto", "duckduckgo", "wikipedia", "arxiv"], 
                                    value="auto",
                                    interactive=True,
                                    container=False,
                                    show_label=False
                                )
                            with gr.Column(scale=6, min_width=0):
                                tdesc = gr.Textbox(lines=2, interactive=True, container=False, show_label=False)
                            
                            task_components.append(row)
                            task_components.append(tid)
                            task_components.append(tsrc)
                            task_components.append(tdesc)
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
                    # Maintain automatic scrolling for the log view.
                    log_output.change(None, None, None, js="""
                        () => {
                            const container = document.querySelector('.log-sidebar div.wrapper');
                            if (container) {
                                container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
                            }
                        }
                    """)

        with gr.Group():
            with gr.Row(elem_classes="header-bar"):
                with gr.Column(scale=4, min_width=0):
                    gr.Markdown("Output")
                with gr.Column(scale=1, min_width=0):
                    copy_btn = gr.Button("Copy Report", size="sm", elem_classes="copy-btn")
            
            output_display = gr.Markdown(value="_Results will appear here..._", elem_classes="output-markdown")
            
            # Simple JS to copy the markdown content by targetting the specific markdown div.
            copy_btn.click(None, None, None, js="""
                () => {
                    const text = document.querySelector('.output-markdown').innerText;
                    navigator.clipboard.writeText(text);
                    alert('Report copied to clipboard!');
                }
            """)
            scroll_helper = gr.HTML(visible=False, sanitize=False)
    
    plan_outputs = task_components + [session_thread, output_display, log_output]
    
    submit_btn.click(
        fn=lambda: [gr.update() for _ in range(8*4)] + ["", "_Orchestrator is planning..._", [{"role": "assistant", "content": "Orchestrator is analyzing the brief and generating a research plan...", "metadata": {"title": "Orchestrator is planning", "status": "pending"}}]],
        outputs=plan_outputs
    ).then(
        fn=run_query,
        inputs=[query_input, session_thread],
        outputs=plan_outputs,
        scroll_to_output=True
    )
    
    query_input.submit(
        fn=lambda: [gr.update() for _ in range(8*4)] + ["", "_Orchestrator is planning..._", [{"role": "assistant", "content": "Orchestrator is analyzing the brief and generating a research plan...", "metadata": {"title": "Orchestrator is planning", "status": "pending"}}]],
        outputs=plan_outputs
    ).then(
        fn=run_query,
        inputs=[query_input, session_thread],
        outputs=plan_outputs,
        scroll_to_output=True
    )

    replan_btn.click(
        fn=replan,
        inputs=[query_input],
        outputs=plan_outputs,
        scroll_to_output=True
    )
    
    value_components = []
    for i in range(1, len(task_components), 4):
        value_components.extend([task_components[i], task_components[i+1], task_components[i+2]])
    
    approve_btn.click(
        fn=approve_plan,
        inputs=[session_thread, log_output] + value_components,
        outputs=[output_display, log_output, scroll_helper],
        scroll_to_output=True
    )
    clear_btn.click(
        fn=clear_ui,
        inputs=[session_thread],
        outputs=[query_input, output_display, session_thread] + task_components + [log_output]
    )

    # Verification Gate Listeners
    verify_btn.click(
        fn=verify_human,
        inputs=[user_answer, target_answer],
        outputs=[gate_ui, main_ui, is_verified, error_msg, target_answer, user_answer, challenge_display]
    )
    user_answer.submit(
        fn=verify_human,
        inputs=[user_answer, target_answer],
        outputs=[gate_ui, main_ui, is_verified, error_msg, target_answer, user_answer, challenge_display]
    )
    iface.load(fn=generate_challenge, outputs=[challenge_display, target_answer])
    
    # Simple JS to stop Enter from bubbling up to the 'Plan Research' button if focus is on task edits
    iface.load(None, None, None, js="""
        () => {
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const active = document.activeElement;
                    if (active && active.tagName === 'TEXTAREA' && active.closest('.approval-group')) {
                        // Let the textarea handle it (e.g. newline if supported) or just stop it
                        e.stopPropagation();
                    }
                }
            }, true);
        }
    """)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", pwa=True, theme=custom_theme, css=custom_css)