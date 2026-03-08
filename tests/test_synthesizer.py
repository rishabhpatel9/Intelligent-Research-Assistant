from src.agents.state import AgentState
from src.agents.nodes.synthesizer import synthesizer_node

def test_synthesizer():
    state = AgentState(
        query="Tell me about dogs and cats.",
        category="",
        plan=[],
        research_findings=[
            {
                "task_id": "task_1",
                "source": "wikipedia",
                "data": "Dogs are domesticated mammals.",
                "pass": True
            },
            {
                "task_id": "task_2",
                "source": "wikipedia",
                "data": "Cats are small carnivorous mammals.",
                "pass": True
            }
        ],
        completed_tasks=["task_1", "task_2"],
        result="",
        messages=[]
    )
    
    new_state = synthesizer_node(state)
    result = new_state.get("result", "")
    
    print("\n[Synthesizer Output]")
    print(result)
    assert "Executive Summary" in result or "Dogs" in result
    
if __name__ == "__main__":
    test_synthesizer()
    print("\nSynthesizer test passed!")
