"""State definition for the research agent."""
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State tracking for the research agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    product_brand: str
    product_name: str
    search_history: List[Dict[str, Any]]  # Stores: query, result, info extracted

