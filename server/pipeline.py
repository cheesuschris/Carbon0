from typing import Any, Dict, List, Optional
import logging
import json

# reuse existing project modules
from server.agents import transform as transform_module
from server.services import carbon_calc
from server import database
from server import recommender

# Try to import arrange agent if present
try:
    from server.agents import arrange as arrange_module
    HAS_ARRANGE = hasattr(arrange_module, "arrange_product")
except Exception:
    HAS_ARRANGE = False

logger = logging.getLogger(__name__)


def _fallback_build_record(product_json: Dict[str, Any],
                           transformed: Dict[str, Any],
                           carbon_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a minimal product record if agents.arrange.arrange_product is not available.
    Produces fields compatible with database.insert_product.
    """
    def _safe(v, default=None):
        return v if v is not None else default

    sku = product_json.get("sku") or product_json.get("id") or None
    name = product_json.get("name") or transformed.get("product_name") or None
    brand = product_json.get("brand") or None
    price_val = product_json.get("price") or None
    # try to normalize price if transform provided numeric product_weight or others
    try:
        import re
        if isinstance(price_val, str):
            m = re.search(r"(\d+(?:[.,]\d{1,2})?)", price_val.replace(",", ""))
            if m:
                price = float(m.group(1))
            else:
                price = None
        elif isinstance(price_val, (int, float)):
            price = float(price_val)
        else:
            price = None
    except Exception:
        price = None

    web_url = product_json.get("url") or product_json.get("web_url") or None
    image_url = product_json.get("image") or product_json.get("image_url") or None

    cf_value = carbon_result.get("cf_total")
    if cf_value is None:
        bd = carbon_result.get("breakdown") or {}
        try:
            cf_value = sum(float(v) for v in bd.values() if v is not None)
        except Exception:
            cf_value = None

    # Build a plain-text cf_detail that lists inputs and results
    parts: List[str] = []
    parts.append("CF DETAIL (fallback):")
    parts.append("Inputs (transformed):")
    try:
        parts.append(json.dumps(transformed, ensure_ascii=False, indent=2))
    except Exception:
        parts.append(str(transformed))

    parts.append("\nCarbon calculation output:")
    parts.append(json.dumps(carbon_result, ensure_ascii=False, indent=2))

    cf_detail_text = "\n".join(parts)

    record = {
        "sku": sku,
        "name": name,
        "category": None,   # unknown in fallback
        "brand": brand,
        "price": price,
        "web_url": web_url,
        "image_url": image_url,
        "cf_value": float(cf_value) if cf_value is not None else None,
        "cf_detail": cf_detail_text,
    }
    return record


def process_and_store_product(product_json: Dict[str, Any],
                              model: Optional[str] = "gemini-2.5-flash-lite",
                              transform_temperature: float = 0.0,
                              arrange_temperature: float = 0.0,
                              max_tokens: int = 1024,
                              recommend_top_k: int = 5,
                              alpha: float = 0.5,
                              beta: float = 0.2,
                              gamma: float = 1.0) -> Dict[str, Any]:
    """
    Full pipeline:
      - transform -> carbon_calc -> arrange -> insert into DB -> recommend
    Returns a dict with keys: status, product (db record), transformed, carbon_result, recommendations, messages
    """
    out: Dict[str, Any] = {"status": "ok", "messages": []}
    transformed = None
    carbon_result = None
    record = None
    recommendations = []

    try:
        # 1) Transform
        out["messages"].append("Calling transform.transform_product")
        transformed = transform_module.transform_product(product_json, model=model, temperature=transform_temperature, max_tokens=max_tokens)
        out["transformed"] = transformed
    except Exception as exc:
        logger.exception("Transform step failed")
        out["status"] = "error"
        out["messages"].append(f"transform error: {exc}")
        return out

    try:
        # 2) Carbon calculation
        out["messages"].append("Calling carbon_calc.calculate_carbon_footprint")
        carbon_result = carbon_calc.calculate_carbon_footprint(transformed)
        out["carbon_result"] = carbon_result
    except Exception as exc:
        logger.exception("Carbon calc failed")
        out["status"] = "error"
        out["messages"].append(f"carbon_calc error: {exc}")
        return out

    try:
        # 3) Arrange - prefer agent if available
        out["messages"].append("Building record via arrange agent (or fallback)")
        if HAS_ARRANGE:
            try:
                record = arrange_module.arrange_product(product_json, transformed, carbon_result, model=model)
            except TypeError:
                # some implementations may have different signature
                record = arrange_module.arrange_product(product_json, transformed, carbon_result)
        else:
            record = _fallback_build_record(product_json, transformed, carbon_result)
        out["record"] = record
    except Exception as exc:
        logger.exception("Arrange step failed - using fallback build")
        record = _fallback_build_record(product_json, transformed, carbon_result)
        out["record"] = record
        out["messages"].append("arrange error: used fallback")

    try:
        # 4) Recommendations: use the inserted record (or local record) as target
        out["messages"].append("Generating recommendations")
        recs = recommender.recommend_products(record,
                                              top_k=recommend_top_k,
                                              alpha=alpha,
                                              beta=beta,
                                              gamma=gamma,
                                              exclude_self=True)
        recommendations = recs
        out["recommendations"] = recommendations
    except Exception as exc:
        logger.exception("Recommendation step failed")
        out["messages"].append(f"recommendation error: {exc}")

    try:
        # 5) Insert into DB
        out["messages"].append("Inserting record into database")
        database.insert_product(record)
    except Exception as exc:
        logger.exception("Database insert failed")
        out["messages"].append(f"db insert error: {exc}")
        # proceed to recommendations even if insert fails

    out["product"] = record
    return out
