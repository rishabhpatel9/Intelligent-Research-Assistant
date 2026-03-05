from fastapi import FastAPI
from pydantic import BaseModel
from src.agents.research_agent import workflow

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
def run_query(request: QueryRequest):
    result = workflow.invoke({"query": request.query})
    return result