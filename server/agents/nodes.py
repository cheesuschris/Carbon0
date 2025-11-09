"""Node functions for carbon data collection workflow."""
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
import json
import re
from datetime import datetime

debug_log: List[Dict[str, Any]] = []

def clear_debug_log():
    """Clear the debug log for a new workflow run."""
    global debug_log
    debug_log.clear()

try:
    from .state import CarbonWorkflowState
    from .tools import get_tools_by_name
    from .prompts import get_system_prompt, get_estimation_prompt
    from agents.carbon_state import get_missing_fields, update_carbon_data, get_carbon_data_status
    from agents.data_extractor import extract_data_from_search, save_product_json
    from agents.search_agent import search_carbon_info, format_search_result
    from agents.planning_agent import plan_next_steps
    from services.llm import call_llm
except ImportError:
    from state import CarbonWorkflowState
    from tools import get_tools_by_name
    from prompts import get_system_prompt, get_estimation_prompt
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from agents.carbon_state import get_missing_fields, update_carbon_data, get_carbon_data_status
    from agents.data_extractor import extract_data_from_search, save_product_json
    from agents.search_agent import search_carbon_info, format_search_result
    from agents.planning_agent import plan_next_steps
    from services.llm import call_llm

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

tools_by_name = get_tools_by_name()
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0,
).bind_tools(list(tools_by_name.values()))


def estimate_missing_data(state: CarbonWorkflowState):
    """Use LLM to estimate missing field values."""
    missing = get_missing_fields(state["carbon_input"])
    if not missing:
        debug_log.append({
            "node": "estimate",
            "timestamp": datetime.now().isoformat(),
            "action": "skip",
            "reason": "no_missing_fields"
        })
        return {"estimated_data": {}}
    
    estimated = {}
    carbon_input = state["carbon_input"].copy()
    
    debug_log.append({
        "node": "estimate",
        "timestamp": datetime.now().isoformat(),
        "action": "start_estimation",
        "missing_fields": missing[:5]
    })
    
    for field in missing[:5]:
        try:
            prompt = get_estimation_prompt(
                state["product_brand"],
                state["product_name"],
                field,
                carbon_input
            )
            
            debug_log.append({
                "node": "estimate",
                "timestamp": datetime.now().isoformat(),
                "action": "estimate_field",
                "field": field,
                "prompt": prompt
            })
            
            response = call_llm(prompt, model="gemini-2.5-flash-lite", temperature=0.2, max_tokens=100)
            value = response.strip()
            
            debug_log.append({
                "node": "estimate",
                "timestamp": datetime.now().isoformat(),
                "action": "estimate_response",
                "field": field,
                "response": value
            })
            
            if value and value.upper() != "UNKNOWN":
                estimated[field] = value
                carbon_input = update_carbon_data(carbon_input, field, value, "LLM estimation")
        except Exception as e:
            debug_log.append({
                "node": "estimate",
                "timestamp": datetime.now().isoformat(),
                "action": "estimate_error",
                "field": field,
                "error": str(e)
            })
            continue
    
    status = get_carbon_data_status(carbon_input)
    debug_log.append({
        "node": "estimate",
        "timestamp": datetime.now().isoformat(),
        "action": "complete",
        "estimated": estimated,
        "completeness_after": status["completeness"]
    })
    
    return {
        "estimated_data": estimated,
        "carbon_input": carbon_input,
        "completeness": status["completeness"]
    }


def call_model(state: CarbonWorkflowState, config: RunnableConfig):
    """Call LLM to plan next action."""
    prompt = get_system_prompt(
        state["product_brand"],
        state["product_name"],
        state["carbon_input"],
        state["search_history"],
        state.get("estimated_data", {})
    )
    
    prompt += "\n\nUse the search tool to find missing information, or provide estimates."
    
    messages = [SystemMessage(content=prompt)]
    messages.extend(state["messages"])
    
    debug_log.append({
        "node": "llm",
        "timestamp": datetime.now().isoformat(),
        "action": "call_model",
        "system_prompt": prompt,
        "message_count": len(messages),
        "search_count": state.get("search_count", 0)
    })
    
    response = model.invoke(messages, config)
    
    response_content = ""
    tool_calls = []
    if hasattr(response, 'content'):
        response_content = response.content
    if hasattr(response, 'tool_calls'):
        tool_calls = response.tool_calls
    
    debug_log.append({
        "node": "llm",
        "timestamp": datetime.now().isoformat(),
        "action": "model_response",
        "response_content": response_content[:500] if response_content else "",
        "tool_calls": [{"name": tc.get("name"), "args": tc.get("args")} for tc in tool_calls] if tool_calls else [],
        "has_tool_calls": len(tool_calls) > 0
    })
    
    return {"messages": [response]}


def call_tool(state: CarbonWorkflowState):
    """Execute search tool, extract data, and save to product.json."""
    outputs = []
    search_history = list(state["search_history"])
    carbon_input = state["carbon_input"].copy()
    estimated_data = state.get("estimated_data", {}).copy()
    missing = get_missing_fields(carbon_input)
    
    last_message = state["messages"][-1]
    
    debug_log.append({
        "node": "tools",
        "timestamp": datetime.now().isoformat(),
        "action": "call_tool_start",
        "has_tool_calls": hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls),
        "missing_fields": missing[:5]
    })
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "search":
                query = tool_call["args"].get("query", "")
                
                debug_log.append({
                    "node": "tools",
                    "timestamp": datetime.now().isoformat(),
                    "action": "search_execute",
                    "query": query
                })
                
                search_data = search_carbon_info(query, num_results=3)
                search_result_text = format_search_result(search_data)
                
                debug_log.append({
                    "node": "tools",
                    "timestamp": datetime.now().isoformat(),
                    "action": "search_result",
                    "query": query,
                    "success": search_data.get("success", False),
                    "result_count": search_data.get("result_count", 0),
                    "result_preview": search_result_text[:500]
                })
                
                search_history.append({
                    "query": query,
                    "result": search_result_text,
                    "search_data": search_data
                })
                
                extraction_result = extract_data_from_search(
                    search_result_text,
                    missing,
                    state["product_brand"],
                    state["product_name"],
                    carbon_input
                )
                
                debug_log.append({
                    "node": "tools",
                    "timestamp": datetime.now().isoformat(),
                    "action": "extract_data",
                    "extracted": extraction_result.get("extracted", {}),
                    "extracted_count": len(extraction_result.get("extracted", {}))
                })
                
                carbon_input = extraction_result.get("updated_data", carbon_input)
                
                product_file = save_product_json(
                    state["product_brand"],
                    state["product_name"],
                    carbon_input
                )
                
                debug_log.append({
                    "node": "tools",
                    "timestamp": datetime.now().isoformat(),
                    "action": "save_product_json",
                    "file": str(product_file) if product_file else None
                })
                
                outputs.append(
                    ToolMessage(
                        content=search_result_text,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
    else:
        debug_log.append({
            "node": "tools",
            "timestamp": datetime.now().isoformat(),
            "action": "no_tool_calls",
            "message_type": type(last_message).__name__
        })
    
    status = get_carbon_data_status(carbon_input)
    
    debug_log.append({
        "node": "tools",
        "timestamp": datetime.now().isoformat(),
        "action": "call_tool_complete",
        "completeness": status["completeness"],
        "search_count": state["search_count"] + 1
    })
    
    return {
        "messages": outputs,
        "search_history": search_history,
        "carbon_input": carbon_input,
        "search_count": state["search_count"] + 1,
        "completeness": status["completeness"],
        "estimated_data": estimated_data
    }


def call_planning_agent(state: CarbonWorkflowState):
    """Call planning agent when searches fail to make educated guesses."""
    missing = get_missing_fields(state["carbon_input"])
    
    if not missing:
        return {
            "carbon_input": state["carbon_input"],
            "estimated_data": state.get("estimated_data", {})
        }
    
    user_context = state.get("user_context", {})
    
    debug_log.append({
        "node": "planning",
        "timestamp": datetime.now().isoformat(),
        "action": "planning_start",
        "missing_fields": missing[:5],
        "search_count": state.get("search_count", 0)
    })
    
    planning_result = plan_next_steps(
        state["product_brand"],
        state["product_name"],
        state["carbon_input"],
        missing,
        state["search_history"],
        user_context,
        execute_searches=True
    )
    
    debug_log.append({
        "node": "planning",
        "timestamp": datetime.now().isoformat(),
        "action": "planning_complete",
        "reasoning": planning_result.get("reasoning", "")[:200],
        "educated_guesses": planning_result.get("educated_guesses", {}),
        "suggested_searches": planning_result.get("suggested_searches", []),
        "confidence": planning_result.get("confidence", "low")
    })
    
    carbon_input = state["carbon_input"].copy()
    estimated_data = state.get("estimated_data", {}).copy()
    
    educated_guesses = planning_result.get("educated_guesses", {})
    for field_path, value in educated_guesses.items():
        carbon_input = update_carbon_data(carbon_input, field_path, value, "planning agent educated guess")
        estimated_data[field_path] = value
    
    if planning_result.get("search_results"):
        for search_item in planning_result["search_results"]:
            extraction_result = extract_data_from_search(
                search_item.get("result", ""),
                missing,
                state["product_brand"],
                state["product_name"],
                carbon_input
            )
            carbon_input = extraction_result.get("updated_data", carbon_input)
    
    save_product_json(
        state["product_brand"],
        state["product_name"],
        carbon_input
    )
    
    status = get_carbon_data_status(carbon_input)
    
    return {
        "carbon_input": carbon_input,
        "estimated_data": estimated_data,
        "completeness": status["completeness"],
        "planning_result": planning_result
    }


def should_continue(state: CarbonWorkflowState) -> str:
    """Decide next step."""
    missing = get_missing_fields(state["carbon_input"])
    
    last_message = state["messages"][-1]
    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    
    decision = "end"
    if not missing:
        decision = "complete"
    elif state["search_count"] >= state["max_searches"]:
        decision = "planning"
    elif has_tool_calls:
        decision = "continue"
    elif state["search_count"] > 0 and not has_tool_calls:
        decision = "planning"
    
    debug_log.append({
        "node": "should_continue",
        "timestamp": datetime.now().isoformat(),
        "action": "decision",
        "missing_count": len(missing),
        "search_count": state["search_count"],
        "max_searches": state["max_searches"],
        "has_tool_calls": has_tool_calls,
        "decision": decision
    })
    
    return decision

