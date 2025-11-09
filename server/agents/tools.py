"""Tools for carbon data collection."""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from agents.search_agent import search_carbon_info, format_search_result
except ImportError:
    from search_agent import search_carbon_info, format_search_result


class SearchQueryInput(BaseModel):
    query: str = Field(description="Search query to find carbon footprint information")


@tool("search", args_schema=SearchQueryInput)
def search(query: str) -> str:
    """Search the web for product carbon footprint information. Returns top 3 results."""
    try:
        search_data = search_carbon_info(query, num_results=3)
        return format_search_result(search_data)
    except Exception as e:
        return f"Error: {str(e)}"


def get_tools():
    return [search]


def get_tools_by_name():
    tools = get_tools()
    return {tool.name: tool for tool in tools}

