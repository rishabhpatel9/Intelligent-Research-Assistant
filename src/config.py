import os
from dotenv import load_dotenv

def load_config():
    # Load configuration from the environment.
    load_dotenv()
    
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    if tracing:
        print("LangSmith Tracing is ENABLED")
    else:
        print("LangSmith Tracing is DISABLED")

