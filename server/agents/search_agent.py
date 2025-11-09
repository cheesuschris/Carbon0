"""Modular search agent for web searches."""
import sys
from pathlib import Path
from typing import List, Dict, Any

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from utils.search import search_web, scrape_page
except ImportError:
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from utils.search import search_web, scrape_page


def search_carbon_info(query: str, num_results: int = 3) -> Dict[str, Any]:
    """Search for carbon footprint information."""
    try:
        links = search_web(query, num_results=num_results)
        if not links:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": "No results found"
            }
        
        results = []
        for i, link in enumerate(links, 1):
            content = scrape_page(link)
            if content:
                results.append({
                    "rank": i,
                    "url": link,
                    "content": content[:2000]
                })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "result_count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": str(e)
        }


def search_general(query: str, num_results: int = 3) -> Dict[str, Any]:
    """General purpose search (e.g., 'where does US export metal from?')."""
    return search_carbon_info(query, num_results)


def format_search_result(search_data: Dict[str, Any]) -> str:
    """Format search result for LLM consumption."""
    if not search_data.get("success"):
        return f"Search failed: {search_data.get('error', 'Unknown error')}"
    
    summary = f"Search: {search_data['query']}\n\n"
    for result in search_data["results"]:
        summary += f"[{result['rank']}] {result['url']}\n{result['content'][:500]}...\n\n"
    
    return summary

