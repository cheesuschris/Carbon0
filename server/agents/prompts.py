"""Prompts for carbon data collection workflow."""
from agents.carbon_state import get_missing_fields, get_carbon_data_status


def get_planning_prompt(brand: str, product: str, carbon_input: dict, missing_fields: list) -> str:
    """Prompt for LLM to plan what to estimate or search for."""
    status = get_carbon_data_status(carbon_input)
    
    prompt = f"""You are analyzing: {brand} {product}

    Current data completeness: {status['completeness']:.1f}%
    Missing fields: {', '.join(missing_fields[:10])}

    Your task:
    1. For missing data, first try to ESTIMATE based on product type and common knowledge
    2. If estimation is uncertain, plan a SEARCH query to find the information

    For estimation, consider:
    - Product type and typical materials used
    - Common manufacturing locations for this product category
    - Typical shipping methods and distances
    - Standard packaging for similar products
    - Industry-standard emission factors

    Return your plan as:
    - ESTIMATE: field_name = value (reasoning)
    - SEARCH: query to find information

    Example:
    ESTIMATE: materials[0].name = "Polyester" (common for office chairs)
    ESTIMATE: transport.mode = "sea" (typical for furniture from Asia)
    SEARCH: {brand} {product} manufacturing location made in
    """
    return prompt


def get_estimation_prompt(brand: str, product: str, field_to_estimate: str, carbon_input: dict) -> str:
    """Prompt for LLM to estimate a specific field value."""
    prompt = f"""Estimate the value for: {field_to_estimate}

    Product: {brand} {product}
    Current data: {str(carbon_input)[:500]}

    Based on the product type and common industry knowledge, estimate this field.
    Return ONLY the estimated value, or "UNKNOWN" if you cannot estimate.

    Field: {field_to_estimate}
    """
    return prompt


def get_extraction_prompt(search_result: str, missing_fields: list, brand: str, product: str) -> str:
    """Prompt to extract data from search results."""
    prompt = f"""Extract carbon footprint data from search results:

    Product: {brand} {product}
    Missing fields: {', '.join(missing_fields[:5])}

    Search result:
    {search_result[:2000]}

    Extract relevant data. Return JSON with field paths as keys.
    Example: {{"transport.origin": "Vietnam", "materials[0].name": "Polyester"}}

    If no data found, return {{}}.
    """
    return prompt


def get_system_prompt(brand: str, product: str, carbon_input: dict, search_history: list, estimated_data: dict) -> str:
    """Main system prompt for the workflow."""
    missing = get_missing_fields(carbon_input)
    status = get_carbon_data_status(carbon_input)
    
    prompt = f"""You are collecting carbon footprint data for: {brand} {product}

    Completeness: {status['completeness']:.1f}%
    Missing: {len(missing)} fields
    Searches made: {len(search_history)}/{10}

    Strategy:
    1. First ESTIMATE missing values based on product knowledge
    2. If uncertain, SEARCH for specific information
    3. Update data as you find or estimate values

    Missing fields: {', '.join(missing[:8]) if missing else 'None'}
    """
    
    if estimated_data:
        prompt += f"\nEstimated so far: {list(estimated_data.keys())[:5]}\n"
    
    if search_history:
        prompt += "\nRecent searches:\n"
        for s in search_history[-3:]:
            prompt += f"- {s.get('query', '')}\n"
    
    return prompt

