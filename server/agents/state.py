"""State definition for carbon data collection workflow."""
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CarbonWorkflowState(TypedDict):
    """State for carbon footprint data collection."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    product_brand: str
    product_name: str
    carbon_input: Dict[str, Any]
    search_history: List[Dict[str, Any]]
    search_count: int
    max_searches: int
    completeness: float
    estimated_data: Dict[str, Any]
    user_context: Dict[str, Any]

