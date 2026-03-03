import requests
import os

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")

def query_llm(messages, model="local-model"):
    """
    Send a chat-style request to LM Studio running locally.
    messages: list of dicts, e.g. [{"role": "user", "content": "Hello"}]
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(LM_STUDIO_URL, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
