"""Extract data from search results and save to product.json."""
import sys
from pathlib import Path
from typing import Dict, Any, List
import json
import re
from datetime import datetime

parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from services.llm import call_llm
    from agents.carbon_state import get_missing_fields, update_carbon_data, get_carbon_data_status
    from agents.prompts import get_extraction_prompt
except ImportError:
    from services.llm import call_llm
    from carbon_state import get_missing_fields, update_carbon_data, get_carbon_data_status
    from prompts import get_extraction_prompt


def extract_data_from_search(
    search_result: str,
    missing_fields: List[str],
    brand: str,
    product: str,
    current_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract carbon data from search results using LLM."""
    if not missing_fields:
        return {"extracted": {}, "updated_data": current_data}
    
    prompt = get_extraction_prompt(search_result, missing_fields, brand, product)
    
    try:
        response = call_llm(prompt, model="gemini-2.5-flash-lite", temperature=0.1, max_tokens=300)
        
        extracted = {}
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            try:
                extracted = json.loads(json_match.group())
            except:
                pass
        
        updated_data = current_data.copy()
        if extracted:
            for field_path, value in extracted.items():
                updated_data = update_carbon_data(updated_data, field_path, value, "retrieved from web")
        
        return {
            "extracted": extracted,
            "updated_data": updated_data,
            "extraction_prompt": prompt[:500],
            "llm_response": response[:500]
        }
    except Exception as e:
        return {
            "extracted": {},
            "updated_data": current_data,
            "error": str(e)
        }


def save_product_json(
    product_brand: str,
    product_name: str,
    carbon_data: Dict[str, Any],
    output_dir: Path = None
) -> Path:
    """Save product data to product.json."""
    if output_dir is None:
        output_dir = Path(__file__).parent
    
    product_file = output_dir / "product.json"
    
    product_info = {
        "product_brand": product_brand,
        "product_name": product_name,
        "carbon_data": carbon_data,
        "last_updated": datetime.now().isoformat(),
        "completeness": get_carbon_data_status(carbon_data)["completeness"]
    }
    
    try:
        with open(product_file, 'w', encoding='utf-8') as f:
            json.dump(product_info, f, indent=2, ensure_ascii=False)
        return product_file
    except Exception as e:
        print(f"Warning: Could not save product.json: {e}")
        return None

