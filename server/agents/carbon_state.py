"""State management for carbon footprint data."""
from typing import Dict, Any, List
import copy


def get_missing_fields(carbon_input: Dict[str, Any]) -> List[str]:
    """Check what carbon footprint data is missing."""
    missing = []
    
    if "materials" not in carbon_input or not carbon_input.get("materials"):
        missing.append("materials")
    else:
        for i, material in enumerate(carbon_input["materials"]):
            if "name" not in material:
                missing.append(f"materials[{i}].name")
            if "weight" not in material:
                missing.append(f"materials[{i}].weight")
            if "emission_factor" not in material:
                missing.append(f"materials[{i}].emission_factor")
    
    if "manufacturing_factor" not in carbon_input:
        missing.append("manufacturing_factor")
    elif "value" not in carbon_input["manufacturing_factor"]:
        missing.append("manufacturing_factor.value")
    
    if "transport" not in carbon_input:
        missing.append("transport")
    else:
        if "origin" not in carbon_input["transport"]:
            missing.append("transport.origin")
        if "distance_km" not in carbon_input["transport"]:
            missing.append("transport.distance_km")
        if "mode" not in carbon_input["transport"]:
            missing.append("transport.mode")
        if "emission_factor_ton_km" not in carbon_input["transport"]:
            missing.append("transport.emission_factor_ton_km")
    
    if "packaging" not in carbon_input:
        missing.append("packaging")
    else:
        if "weight" not in carbon_input["packaging"]:
            missing.append("packaging.weight")
        if "emission_factor" not in carbon_input["packaging"]:
            missing.append("packaging.emission_factor")
    
    if "product_weight" not in carbon_input:
        missing.append("product_weight")
    elif "value" not in carbon_input["product_weight"]:
        missing.append("product_weight.value")
    
    return missing


def update_carbon_data(carbon_input: Dict[str, Any], field_path: str, value: Any, source: str = "retrieved from web") -> Dict[str, Any]:
    """Update carbon input data with new information."""
    updated = copy.deepcopy(carbon_input)
    
    if "." in field_path:
        parts = field_path.split(".")
        current = updated
        
        for part in parts[:-1]:
            if "[" in part and "]" in part:
                key, index = part.split("[")
                index = int(index.rstrip("]"))
                if key not in current:
                    current[key] = []
                while len(current[key]) <= index:
                    current[key].append({})
                current = current[key][index]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        last_part = parts[-1]
        if "[" in last_part and "]" in last_part:
            key, index = last_part.split("[")
            index = int(index.rstrip("]"))
            if key not in current:
                current[key] = []
            while len(current[key]) <= index:
                current[key].append({})
            current[key][index] = value
        else:
            current[last_part] = value
            source_key = f"{last_part}_source"
            if source_key not in current:
                current[source_key] = source
    else:
        updated[field_path] = value
        source_key = f"{field_path}_source"
        if source_key not in updated:
            updated[source_key] = source
    
    return updated


def get_carbon_data_status(carbon_input: Dict[str, Any]) -> Dict[str, Any]:
    """Get status of carbon data."""
    missing = get_missing_fields(carbon_input)
    total_fields = 20
    filled_fields = total_fields - len(missing)
    completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    
    return {
        "available": [k for k in carbon_input.keys() if k not in ["materials"]],
        "missing": missing,
        "completeness": round(completeness, 1),
        "has_materials": "materials" in carbon_input and len(carbon_input.get("materials", [])) > 0
    }

