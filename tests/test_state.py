from src.agents.state import AgentState

def test_agent_state_annotations():
    # Verify that we can instantiate it and that the annotations are present
    annotations = AgentState.__annotations__
    assert "query" in annotations
    assert "research_findings" in annotations
    assert "completed_tasks" in annotations

def test_workflow_compiles():
    # Verify that the graph still compiles with the new checkpointer and state
    from src.agents.research_agent import workflow
    assert workflow is not None

if __name__ == "__main__":
    test_agent_state_annotations()
    test_workflow_compiles()
    print("All tests passed successfully!")
