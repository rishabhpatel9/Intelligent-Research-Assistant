from src.agents.state import AgentState
from src.agents.nodes.reader import reader_node

def test_reader():
    state = AgentState(
        query="What is python?",
        category="",
        plan=[],
        research_findings=[
            {
                "task_id": "task_1",
                "query": "Python programming",
                "source": "duckduckgo",
                "data": "[Duckduckgo Results]\n- Python overview\n  A programming language\n  https://www.python.org/"
            }
        ],
        completed_tasks=["task_1"],
        result="",
        messages=[]
    )
    
    new_state = reader_node(state)
    findings = new_state.get("research_findings", [])
    
    assert "scraped_data" in findings[0]
    
    print("\n[Reader Output]")
    print(findings[0]["scraped_data"][:200] + "...")
    
if __name__ == "__main__":
    test_reader()
    print("\nReader test passed!")
