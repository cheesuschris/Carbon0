from typing import Any, Dict, List, Optional, Tuple
import math
import logging

# Optional: use database helper to fetch candidates
from server.database import get_all_products

def _tokenize(s: Optional[str]) -> List[str]:
    if not s:
        return []
    import re
    s2 = s.lower().replace("_", " ").replace("-", " ")
    return re.findall(r"[a-z0-9]+", s2)

def category_similarity(target: Dict[str, Any], candidate: Dict[str, Any]) -> float:
    """
    Compute a category/brand/name similarity in [0,1].
    Strategy:
      - if categories equal and not None -> 1.0
      - else if brands equal and not None -> 0.6
      - else fallback to token overlap on names (Jaccard-like) scaled to [0,0.8]
    """
    t_cat = target.get("category")
    c_cat = candidate.get("category")
    if t_cat and c_cat and t_cat == c_cat:
        return 1.0

    t_brand = (target.get("brand") or "").strip().lower()
    c_brand = (candidate.get("brand") or "").strip().lower()
    if t_brand and c_brand and t_brand == c_brand:
        return 0.6

    # token overlap on product names
    t_name_tokens = set(_tokenize(target.get("name") or ""))
    c_name_tokens = set(_tokenize(candidate.get("name") or ""))
    if not t_name_tokens or not c_name_tokens:
        return 0.0
    inter = t_name_tokens.intersection(c_name_tokens)
    union = t_name_tokens.union(c_name_tokens)
    jaccard = len(inter) / len(union) if union else 0.0
    # scale jaccard to a conservative max, e.g., up to 0.5
    return min(0.8, jaccard * 0.8)

def price_similarity(p1: Optional[float], p2: Optional[float]) -> float:
    """
    1 - abs(p1-p2)/max(p1,p2), clamped to [0,1].
    If either price missing or zero -> return a neutral 0.5 (you can change policy).
    """
    try:
        if p1 is None or p2 is None:
            return 0.5
        if p1 <= 0 or p2 <= 0:
            return 0.5
        diff = abs(p1 - p2)
        denom = max(p1, p2)
        sim = 1.0 - (diff / denom)
        return max(0.0, min(1.0, sim))
    except Exception:
        return 0.5

def _normalize_list(values: List[Optional[float]], missing_as_max: bool = True) -> List[float]:
    """
    Normalize values to [0,1].
    - None values: if missing_as_max True -> treated as max(value) (worst); else treated as median.
    Returns list of floats in [0,1].
    """
    vals = [v for v in values if v is not None and (isinstance(v, (int, float)) and not math.isnan(v))]
    if not vals:
        return [1.0 if missing_as_max else 0.5 for _ in values]
    vmin = min(vals)
    vmax = max(vals)
    normed = []
    for v in values:
        if v is None or not isinstance(v, (int, float)) or math.isnan(v):
            if missing_as_max:
                # worst case: normalize to 1.0
                normed.append(1.0)
            else:
                # approximate with median
                median = sorted(vals)[len(vals)//2]
                if vmax == vmin:
                    normed.append(0.0 if median == vmin else 0.5)
                else:
                    normed.append((median - vmin) / (vmax - vmin))
            continue
        if vmax == vmin:
            normed.append(0.0)  # all equal -> best (lowest) maps to 0.0
        else:
            normed.append((v - vmin) / (vmax - vmin))
    return normed

def compute_scores(target: Dict[str, Any],
                   candidates: List[Dict[str, Any]],
                   alpha: float = 0.5,
                   beta: float = 0.2,
                   gamma: float = 1.0,
                   missing_cf_as_max: bool = True) -> List[Tuple[Dict[str, Any], float, dict]]:
    """
    Compute recommendation scores for each candidate.
    Returns list of tuples (candidate, score, debug_info).
    Note: gamma is applied to normalized carbon_emission (higher raw cf -> higher normalized -> larger subtraction).
    """
    # gather cf_values for normalization
    cf_values = [c.get("cf_value") for c in candidates]
    normalized_cf = _normalize_list(cf_values, missing_as_max=missing_cf_as_max)
    results: List[Tuple[Dict[str, Any], float, dict]] = []

    # build index map for normalized cf
    for i, cand in enumerate(candidates):
        cat_sim = category_similarity(target, cand)
        p_sim = price_similarity(_safe_price(target.get("price")), _safe_price(cand.get("price")))
        norm_cf = normalized_cf[i]  # in [0,1], 0 = lowest cf (best), 1 = highest (worst)

        # according to your formula: score = α*cat_sim + β*price_sim - γ*carbon_emission
        score = alpha * cat_sim + beta * p_sim - gamma * norm_cf

        debug = {
            "category_similarity": cat_sim,
            "price_similarity": p_sim,
            "normalized_cf": norm_cf,
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma
        }
        results.append((cand, score, debug))

    # sort descending by score
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def recommend_products(target: Dict[str, Any],
                       candidates: Optional[List[Dict[str, Any]]] = None,
                       top_k: int = 10,
                       alpha: float = 0.5,
                       beta: float = 0.2,
                       gamma: float = 1.0,
                       missing_cf_as_max: bool = True,
                       exclude_self: bool = True) -> List[Dict[str, Any]]:
    """
    Return top_k candidate dicts (with score and debug) sorted by score.
    If candidates not provided, fetches all from DB (get_all_products).
    """
    if candidates is None:
        candidates = get_all_products()

    # optionally exclude the target itself by SKU
    target_sku = target.get("sku")
    filtered = []
    for c in candidates:
        if exclude_self and target_sku and c.get("sku") and c.get("sku") == target_sku:
            continue
        filtered.append(c)

    scored = compute_scores(target, filtered, alpha=alpha, beta=beta, gamma=gamma, missing_cf_as_max=missing_cf_as_max)
    # prepare output with candidate info and score/debug
    out = []
    for cand, score, debug in scored[:top_k]:
        entry = dict(cand)  # shallow copy
        entry["_rec_score"] = score
        entry["_rec_debug"] = debug
        out.append(entry)
    return out

# Helpers
def _safe_price(p: Optional[Any]) -> Optional[float]:
    """
    Try to coerce stored price to float. If already float/int -> return.
    If string like "$79.99" or "79.99 USD" -> extract numeric.
    """
    if p is None:
        return None
    try:
        if isinstance(p, (int, float)):
            return float(p)
        s = str(p)
        import re
        m = re.search(r"(\d+(?:[.,]\d{1,2})?)", s.replace(",", ""))
        if not m:
            return None
        return float(m.group(1))
    except Exception:
        return None
