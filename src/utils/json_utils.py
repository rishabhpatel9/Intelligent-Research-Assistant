import json
import re
from json_repair import repair_json

def parse_json_robustly(raw_text: str):
    #Parse JSON content from text, handling common formatting issues.
    if not raw_text:
        return None

    # Remove markdown formatting and extra whitespace.
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Find the bounds of the JSON content.
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

    # Repair and parse the JSON string.
    try:
        repaired = repair_json(text)
        data = json.loads(repaired)
        # We only want lists or dicts, not string literals
        if not isinstance(data, (list, dict)):
            return None
        return data
    except Exception as e:
        # Standard parsing fallback.
        try:
            data = json.loads(text)
            if not isinstance(data, (list, dict)):
                return None
            return data
        except Exception:
            raise e
