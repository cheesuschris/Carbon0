from langchain_core.tools import tool
from pydantic import BaseModel, Field
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from utils.search import search_web, scrape_page

class SearchQueryInput(BaseModel):
    query: str = Field(
        description="The search query to find information about the product. "
        "Be specific about what you're looking for."
    )

@tool("search", args_schema=SearchQueryInput)
def search(query: str) -> str:    
    """
    Search the web for product information. Returns top 5 results with content.
    """
    try:
        links = search_web(query, num_results=3)
        if not links:
            return f"No results found for: {query}"
        
        results = []
        for i, link in enumerate(links, 1):
            content = scrape_page(link)
            if content:
                results.append({
                    "rank": i,
                    "url": link,
                    "content": content
                })
        
        if not results:
            return f"Found {len(links)} links but couldn't scrape content"

        # Format summary
        """summary = f"Search: {query}\n\n"
        for result in results:
            summary += f"[{result['rank']}] {result['url']}\n{result['content'][:500]}...\n\n"
        
        return summary"""
        return results
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"

def get_tools():
    """Get all available tools."""
    return [search]

def get_tools_by_name():
    """Get a dictionary mapping tool names to tools."""
    tools = get_tools()
    return {tool.name: tool for tool in tools}

if __name__ == "__main__":
    # Test the search tool
    print("Testing search tool...")
    result = search.invoke({"query": "Sweetcrispy Ergonomic Office Desk Chair Mesh Adjustable Swivel Mid-Back Computer Chair with Lumbar Support Comfy Flip-up Arms for Home Office"})

    print(result)