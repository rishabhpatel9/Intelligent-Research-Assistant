import requests
import os

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")

def query_llm(messages, model="qwen3.5-2b", temperature=0.7):
    """
    Args:
        messages (list): Conversation history in OpenAI-style format.
                        Example: [{"role": "user", "content": "Hello"}]
        model (str): Model name configured in LM Studio.
        temperature (float): Sampling temperature for creativity.

    Returns:
        str: The assistant's reply content.
    """
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM Error] {str(e)}"
