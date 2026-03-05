import gradio as gr
import requests
import os

# Default to local FastAPI backend, override in deployment
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/query")

def run_query(query: str):
    response = requests.post(API_URL, json={"query": query})
    if response.status_code == 200:
        data = response.json()
        return f"Category: {data['category']}\n\nResult:\n{data['result']}"
    else:
        return f"Error: {response.status_code}"

iface = gr.Interface(
    fn=run_query,
    inputs=gr.Textbox(lines=2, placeholder="Enter your query here..."),
    outputs="text",
    title="Intelligent Research Assistant",
    description="Ask questions, get search, summaries, fact-checks, or hybrid results."
)

if __name__ == "__main__":
    iface.launch()