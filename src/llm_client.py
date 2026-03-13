import requests
import os

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")

def query_llm(messages, model="qwen3.5-2b", temperature=0.7, json_mode=False):
    # Send messages to the language model and return the response.
    def _make_request(current_model, use_json):
        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": temperature
        }
        if use_json:
            payload["response_format"] = {"type": "json_object"}
            
        try:
            response = requests.post(LM_STUDIO_URL, json=payload, timeout=60)
            if response.status_code != 200:
                print(f"[LLM] Server returned error {response.status_code}: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise e

    # Attempt to get a response from the model with automatic fallbacks.
    try:
        return _make_request(model, json_mode)
    except Exception as e:
        if json_mode:
            try:
                print(f"[LLM] JSON mode failed for {model}, retrying with plain text...")
                return _make_request(model, False)
            except Exception:
                pass # Continue to model fallback
        
        if model == "qwen3.5-2b":
            print(f"[LLM] Falling back to qwen3.5-0.8b. Original Error: {str(e)}")
            try:
                return _make_request("qwen3.5-0.8b", False)
            except Exception as e2:
                return f"[LLM Error] Fallback also failed: {str(e2)}"
        return f"[LLM Error] {str(e)}"
