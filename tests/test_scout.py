from src.agents.state import AgentState
from src.agents.nodes.scout import scout_node

def test_scout():
    # Mocking a state output from the Orchestrator
    state = AgentState(
        query="What is the capital of Japan and what are its demographics?",
        category="",
        plan=[
            {"id": "task_1", "description": "Capital of Japan", "source": "wikipedia"}
        ],
        research_findings=[],
        completed_tasks=[],
        result="",
        messages=[]
    )
    
    new_state = scout_node(state)
    findings = new_state.get("research_findings", [])
    completed = new_state.get("completed_tasks", [])
    
    assert len(findings) == 1
    assert completed == ["task_1"]
    assert "Wikipedia Results" in findings[0]["data"] or "Cached" in findings[0]["data"]
    
    print("\n[Scout Output]")
    print(findings[0]["data"])
    
if __name__ == "__main__":
    test_scout()
    print("\nScout test passed!")
