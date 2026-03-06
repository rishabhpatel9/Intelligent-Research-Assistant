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
    def _make_request(current_model):
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": temperature
        }
        response = requests.post(LM_STUDIO_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    try:
        return _make_request(model)
    except Exception as e:
        if model == "qwen3.5-2b":
            print(f"Failed to use {model}, falling back to qwen3.5-0.8b. Error: {str(e)}")
            try:
                return _make_request("qwen3.5-0.8b")
            except Exception as e2:
                return f"[LLM Error] Fallback also failed: {str(e2)}"
        return f"[LLM Error] {str(e)}"
