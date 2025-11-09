"""Main workflow for carbon data collection."""
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from langchain_core.messages import HumanMessage

try:
    from agents.carbon_state import get_missing_fields, get_carbon_data_status
    from .graph import graph
    from .state import CarbonWorkflowState
    from .nodes import debug_log
except ImportError:
    from carbon_state import get_missing_fields, get_carbon_data_status
    from graph import graph
    from state import CarbonWorkflowState
    from nodes import debug_log

debug_steps: List[Dict[str, Any]] = []


def collect_carbon_data(
    product_brand: str,
    product_name: str,
    carbon_input: Dict[str, Any],
    max_searches: int = 10,
    user_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Collect carbon footprint data with estimation and searching."""
    missing = get_missing_fields(carbon_input)
    
    if not missing:
        status = get_carbon_data_status(carbon_input)
        return {
            "carbon_data": carbon_input,
            "search_history": [],
            "completeness": status["completeness"],
            "completeness_achieved": True,
            "summary": "All data already present"
        }
    
    debug_steps.clear()
    try:
        from .nodes import clear_debug_log
    except:
        from nodes import clear_debug_log
    clear_debug_log()
    
    debug_steps.append({
        "step": "initialization",
        "timestamp": datetime.now().isoformat(),
        "missing_fields": missing,
        "initial_carbon_input": carbon_input.copy(),
        "message": f"Starting workflow with {len(missing)} missing fields"
    })
    
    initial_state: CarbonWorkflowState = {
        "messages": [
            HumanMessage(
                content=f"Collect carbon footprint data for {product_brand} {product_name}. "
                f"Missing: {', '.join(missing[:5])}"
            )
        ],
        "product_brand": product_brand,
        "product_name": product_name,
        "carbon_input": carbon_input.copy() if carbon_input else {},
        "search_history": [],
        "search_count": 0,
        "max_searches": max_searches,
        "completeness": 0.0,
        "estimated_data": {},
        "user_context": user_context or {}
    }
    
    final_state = None
    step_count = 0
    for state in graph.stream(initial_state, stream_mode="values"):
        step_count += 1
        final_state = state
        
        debug_steps.append({
            "step": f"workflow_step_{step_count}",
            "timestamp": datetime.now().isoformat(),
            "node": "state_update",
            "search_count": state.get("search_count", 0),
            "completeness": state.get("completeness", 0.0),
            "missing_fields": get_missing_fields(state.get("carbon_input", {})),
            "carbon_input_snapshot": state.get("carbon_input", {}).copy(),
            "estimated_data": state.get("estimated_data", {}).copy(),
            "search_history_count": len(state.get("search_history", []))
        })
    
    if not final_state:
        return {
            "carbon_data": carbon_input,
            "search_history": [],
            "completeness": 0.0,
            "completeness_achieved": False,
            "summary": "Workflow failed"
        }
    
    final_missing = get_missing_fields(final_state["carbon_input"])
    completeness_achieved = len(final_missing) == 0
    
    summary = f"Collected {final_state['completeness']:.1f}% of data"
    if completeness_achieved:
        summary = "All data collected successfully"
    elif final_state["search_count"] >= max_searches:
        summary += f" (max searches {max_searches} reached)"
    
    try:
        from .nodes import debug_log as node_debug_log
    except:
        from nodes import debug_log as node_debug_log
    
    debug_data = {
        "product_brand": product_brand,
        "product_name": product_name,
        "initial_carbon_input": carbon_input,
        "final_carbon_input": final_state["carbon_input"],
        "search_history": final_state["search_history"],
        "estimated_data": final_state.get("estimated_data", {}),
        "search_count": final_state["search_count"],
        "completeness": final_state["completeness"],
        "completeness_achieved": completeness_achieved,
        "missing_fields": final_missing,
        "workflow_steps": debug_steps,
        "node_debug_log": node_debug_log.copy(),
        "total_steps": step_count
    }
    
    debug_file = Path(__file__).parent / "carbon_debug.json"
    try:
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        print(f"\nDebug data saved to: {debug_file}")
    except Exception as e:
        print(f"Warning: Could not save debug file: {e}")
    
    return {
        "carbon_data": final_state["carbon_input"],
        "search_history": final_state["search_history"],
        "completeness": final_state["completeness"],
        "completeness_achieved": completeness_achieved,
        "summary": summary,
        "estimated_data": final_state.get("estimated_data", {})
    }


if __name__ == "__main__":
    test_input = {
        "product_weight": {"value": 0.6, "source": "from extension"}
    }
    
    user_context = {
        "location": "Princeton, NJ, USA"
    }
    
    result = collect_carbon_data(
        "Sweetcrispy",
        "Ergonomic Office Desk Chair",
        test_input,
        max_searches=5,
        user_context=user_context
    )
    
    print(f"\nCompleteness: {result['completeness']:.1f}%")
    print(f"Achieved: {result['completeness_achieved']}")
    print(f"Summary: {result['summary']}")
    print(f"Searches: {len(result['search_history'])}")
    print(f"\nCarbon Data:\n{json.dumps(result['carbon_data'], indent=2)}")

