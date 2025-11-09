"""Planning agent for educated guesses and strategic planning."""
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
import re

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from services.llm import call_llm
    from agents.carbon_state import get_missing_fields
    from agents.search_agent import search_general, format_search_result
except ImportError:
    from services.llm import call_llm
    from carbon_state import get_missing_fields
    from search_agent import search_general, format_search_result


def create_planning_prompt(
    brand: str,
    product: str,
    carbon_data: Dict[str, Any],
    missing_fields: List[str],
    search_history: List[Dict[str, Any]],
    user_context: Dict[str, Any] = None
) -> str:
    """Create prompt for planning agent to make educated guesses."""
    user_location = user_context.get("location", "unknown") if user_context else "unknown"
    
    prompt = f"""You are a carbon footprint planning agent. Your task is to analyze what information is missing and make educated guesses based on available context.

Product: {brand} {product}

Current Carbon Data:
{json.dumps(carbon_data, indent=2)}

Missing Fields:
{', '.join(missing_fields[:10])}

Search History ({len(search_history)} searches):
"""
    for i, search in enumerate(search_history[-3:], 1):
        prompt += f"{i}. Query: {search.get('query', 'N/A')}\n"
    
    prompt += f"""
User Context:
- Location: {user_location}
- You can use this to infer manufacturing locations, transport routes, etc.

Your task:
1. Analyze what's missing and why previous searches might have failed
2. Think in first person: "I saw that the user is in {user_location}, so products of these materials are usually made in..."
3. Make educated guesses about:
   - Where materials might come from (e.g., "If user is in Princeton, US, and this is metal, US typically imports metal from...")
   - Typical transport routes and modes
   - Average emission factors for similar products
   - Common manufacturing locations for this product type

4. Suggest specific search queries that would help find:
   - General patterns (e.g., "where does US export metal from?")
   - Industry averages
   - Typical supply chains for this product category

Respond in JSON format:
{{
  "reasoning": "Your first-person reasoning about what you know and what you can infer",
  "educated_guesses": {{
    "field_path": "estimated_value",
    ...
  }},
  "suggested_searches": [
    "query 1",
    "query 2"
  ],
  "confidence": "high/medium/low"
}}
"""
    return prompt


def plan_next_steps(
    brand: str,
    product: str,
    carbon_data: Dict[str, Any],
    missing_fields: List[str],
    search_history: List[Dict[str, Any]],
    user_context: Dict[str, Any] = None,
    execute_searches: bool = True
) -> Dict[str, Any]:
    """Plan next steps with educated guesses."""
    prompt = create_planning_prompt(brand, product, carbon_data, missing_fields, search_history, user_context)
    
    try:
        response = call_llm(prompt, model="gemini-2.5-flash", temperature=0.3, max_tokens=500)
        
        planning_result = {
            "prompt": prompt,
            "llm_response": response,
            "educated_guesses": {},
            "suggested_searches": [],
            "reasoning": "",
            "confidence": "low"
        }
        
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                planning_result.update({
                    "educated_guesses": parsed.get("educated_guesses", {}),
                    "suggested_searches": parsed.get("suggested_searches", []),
                    "reasoning": parsed.get("reasoning", ""),
                    "confidence": parsed.get("confidence", "low")
                })
            except:
                pass
        
        if execute_searches and planning_result["suggested_searches"]:
            search_results = []
            for query in planning_result["suggested_searches"][:2]:
                result = search_general(query, num_results=2)
                search_results.append({
                    "query": query,
                    "result": format_search_result(result)
                })
            planning_result["search_results"] = search_results
        
        return planning_result
    except Exception as e:
        return {
            "error": str(e),
            "educated_guesses": {},
            "suggested_searches": []
        }

