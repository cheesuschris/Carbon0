"""Graph definition for carbon data collection workflow."""
from langgraph.graph import StateGraph, END

try:
    from .state import CarbonWorkflowState
    from .nodes import call_model, call_tool, should_continue, estimate_missing_data, call_planning_agent
except ImportError:
    from state import CarbonWorkflowState
    from nodes import call_model, call_tool, should_continue, estimate_missing_data, call_planning_agent


def create_graph():
    """Create and compile the workflow graph."""
    workflow = StateGraph(CarbonWorkflowState)
    
    def estimate_node(state: CarbonWorkflowState):
        return estimate_missing_data(state)
    
    workflow.add_node("estimate", estimate_node)
    workflow.add_node("llm", call_model)
    workflow.add_node("tools", call_tool)
    workflow.add_node("planning", call_planning_agent)
    
    workflow.set_entry_point("estimate")
    workflow.add_edge("estimate", "llm")
    
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "continue": "tools",
            "complete": END,
            "max_reached": "planning",
            "planning": "planning",
            "end": END
        }
    )
    
    workflow.add_edge("tools", "llm")
    workflow.add_edge("planning", END)
    
    return workflow.compile()


graph = create_graph()

