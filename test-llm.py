from src.llm_client import query_llm

if __name__ == "__main__":
    messages = [{"role": "user", "content": "Hello, can you summarize what AI is?"}]
    reply = query_llm(messages)
    print("Model reply:", reply)