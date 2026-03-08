from src.agents.state import AgentState
from src.agents.nodes.orchestrator import orchestrator_node

def test_orchestrator():
    state = AgentState(
        query="Analyze the impact of remote work on commercial real estate in SF and NYC.",
        category="",
        plan=[],
        research_findings=[],
        completed_tasks=[],
        result="",
        messages=[]
    )
    
    new_state = orchestrator_node(state)
    plan = new_state.get("plan", [])
    
    print("\n[Orchestrator Plan Generated]")
    for t in plan:
        print(f"- [{t.get('source', 'auto')}] {t.get('description', '')}")
        
    assert len(plan) > 0, "Plan should have at least one task"
    assert isinstance(plan[0], dict), "Tasks must be dictionaries"
    
if __name__ == "__main__":
    test_orchestrator()
    print("\nOrchestrator test passed!")
