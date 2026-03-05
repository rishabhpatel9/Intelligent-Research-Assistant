import gradio as gr
import requests
import os

# Default to local FastAPI backend, override in deployment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")

def run_query(query: str):
    if not query.strip():
        return "Please enter a query!"
        
    try:
        response = requests.post(API_URL, json={"query": query})
        if response.status_code == 200:
            data = response.json()
            category = data.get('category', 'Unknown')
            result_content = data.get('result', '')
            
            # Format the output using markdown
            return f"Query Category: {category}\n\n---\n\n{result_content}"
        else:
            return f"Error {response.status_code}: Could not process the query."
    except requests.exceptions.RequestException as e:
        return f"Error connecting to the backend: {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Theme
custom_theme = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="gray",
    neutral_hue="slate"
)

# Custom CSS for spacing, maximum width, and better reading experience
custom_css = """
.research-container {
    max-width: 800px !important;
    margin: 0 auto !important;
    padding-top: 2rem !important;
}
.output-markdown {
    padding: 1.5rem;
    border-radius: 8px;
    background-color: var(--background-fill-secondary);
    border: 1px solid var(--border-color-primary);
    min-height: 200px;
}
"""

with gr.Blocks(title="Intelligent Research Assistant") as iface:
    
    with gr.Column(elem_classes="research-container"):
        gr.Markdown(
            """
            <h1 style="text-align: center;">Intelligent Research Assistant</h1>
            
            Welcome to your research hub. Ask questions, request fact checks, summarize long texts, or synthesize multiple sources. 
            The system automatically categorizes and handles your request.
            """
        )
        
        with gr.Group():
            query_input = gr.Textbox(
                lines=5,
                placeholder="Enter your research query or paste text here...",
                label="Research Query"
            )
            
            with gr.Row():
                submit_btn = gr.Button("Analyze", variant="primary", scale=2)
                clear_btn = gr.Button("Clear", variant="secondary", scale=1)
                
        gr.Markdown("### Results")
        
        output_display = gr.Markdown(
            value="_Results will appear here..._", 
            elem_classes="output-markdown"
        )
        
        with gr.Accordion("Examples", open=False):
            gr.Examples(
                examples=[
                    "Summarize the impact of quantum computing on cryptography.",
                    "Fact check: Did humans land on Mars in 2020?",
                    "Find the latest research papers on CRISPR-Cas9."
                ],
                inputs=query_input
            )
        
        # Event listeners
        submit_btn.click(
            fn=run_query,
            inputs=query_input,
            outputs=output_display
        )
        
        # Also allow submitting by pressing Command/Ctrl + Enter inside Textbox
        query_input.submit(
            fn=run_query,
            inputs=query_input,
            outputs=output_display
        )
        
        # Clear functionality
        clear_btn.click(
            fn=lambda: ("", "_Results will appear here..._"),
            inputs=None,
            outputs=[query_input, output_display]
        )

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", pwa=True, theme=custom_theme, css=custom_css)
