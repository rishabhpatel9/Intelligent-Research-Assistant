import requests
import os

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")

# Track models/endpoints that don't support the OpenAI-style json_object mode
# to avoid repeated 400 errors and retries.
_unsupported_json_models = set()

def query_llm(messages, model="qwen3.5-2b", temperature=0.7, json_mode=False):
    # Send messages to the language model and return the response.
    
    # Check if we already know this model doesn't support JSON mode
    effective_json_mode = json_mode and model not in _unsupported_json_models

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
                # If the server explicitly rejects the response_format type, 
                # we want to handle it as a specific error we can catch.
                if response.status_code == 400 and "response_format.type" in response.text:
                    raise ValueError("JSON_MODE_NOT_SUPPORTED")
                
                print(f"[LLM] Server returned error {response.status_code}: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise e

    # Attempt to get a response from the model with automatic fallbacks.
    try:
        return _make_request(model, effective_json_mode)
    except Exception as e:
        if effective_json_mode:
            try:
                # If it was a JSON mode issue, mark the model and retry silently
                if "JSON_MODE_NOT_SUPPORTED" in str(e):
                    _unsupported_json_models.add(model)
                else:
                    print(f"[LLM] JSON mode failed for {model}, retrying with plain text...")
                
                return _make_request(model, False)
            except Exception:
                pass # Continue to model fallback
        
        if model == "qwen3.5-2b" or model not in ["qwen3.5-0.8b"]:
            # Only fallback if we are not already at the smallest model
            fallback_model = "qwen3.5-0.8b"
            if model != fallback_model:
                print(f"[LLM] Falling back to {fallback_model}. Original Error: {str(e)}")
                try:
                    return _make_request(fallback_model, False)
                except Exception as e2:
                    return f"[LLM Error] Fallback also failed: {str(e2)}"
        
        return f"[LLM Error] {str(e)}"
