import json
import re
from json_repair import repair_json

def parse_json_robustly(raw_text: str):
    """
    Attempts to parse JSON from raw text robustly.
    Handles markdown wrappers, trailing commas, and common LLM hallucinations.
    Uses json_repair for deep fixes.
    """
    if not raw_text:
        return None

    # 1. Clean markdown wrappers and whitespace
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # 2. Extract the first JSON structure found (either object or array)
    # This helps if there is leading/trailing conversational text
    start_bracket = text.find('[')
    start_brace = text.find('{')
    
    start = -1
    if start_bracket != -1 and start_brace != -1:
        start = min(start_bracket, start_brace)
    elif start_bracket != -1:
        start = start_bracket
    elif start_brace != -1:
        start = start_brace
        
    if start == -1:
        # If no brackets are found, it's probably not structured JSON content
        return None

    end_bracket = text.rfind(']')
    end_brace = text.rfind('}')
    end = max(end_bracket, end_brace)
    
    if end == -1 or end < start:
        return None
        
    text = text[start:end+1]

    # 3. Handle common LLM escaping hallucinations (e.g. \" used as delimiters)
    text = text.replace('\\"', '"')

    # 4. Use json_repair for final cleanup (handles trailing commas, missing quotes, etc.)
    try:
        repaired = repair_json(text)
        data = json.loads(repaired)
        # We only want lists or dicts, not string literals
        if not isinstance(data, (list, dict)):
            return None
        return data
    except Exception as e:
        # Fallback to standard json.loads if repair failed or produced invalid json
        try:
            data = json.loads(text)
            if not isinstance(data, (list, dict)):
                return None
            return data
        except Exception:
            raise e
