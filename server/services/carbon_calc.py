def _safe_float(value, default=0.0):
    """
    Convert potentially missing/invalid numeric inputs to floats.
    Falls back to default (0.0) when the LLM left the field empty.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_carbon_footprint(data):
    data = data or {}

    materials = data.get("materials") or []
    cf_material = 0.0
    for material in materials:
        material = material or {}
        weight = _safe_float(material.get("weight"))
        emission_factor = _safe_float(material.get("emission_factor"))
        cf_material += weight * emission_factor

    manufacturing_factor = (data.get("manufacturing_factor") or {}).get("value")
    cf_manufacturing = cf_material * _safe_float(manufacturing_factor)

    transport = data.get("transport") or {}
    product_weight = (data.get("product_weight") or {}).get("value")
    cf_transport = (
        _safe_float(product_weight)
        * _safe_float(transport.get("distance_km"))
        * _safe_float(transport.get("emission_factor_ton_km"))
        / 1000
    )

    packaging = data.get("packaging") or {}
    cf_packaging = (
        _safe_float(packaging.get("weight")) * _safe_float(packaging.get("emission_factor"))
    )

    cf_total = cf_material + cf_manufacturing + cf_transport + cf_packaging

    return {
        "cf_total": cf_total,
        "breakdown": {
            "material": cf_material,
            "manufacturing": cf_manufacturing,
            "transport": cf_transport,
            "packaging": cf_packaging,
        }
    }
