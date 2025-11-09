from typing import Optional, Any, Dict
import json
import re

from server.services.llm import call_llm

PROMPT_TEMPLATE = """
You are a data transformation agent that converts raw e-commerce product information into a structured JSON input
for carbon footprint calculation.

You will receive a product dictionary with fields like:
platform, url, image, name, price, rating, shipper, seller, reviews, shippingFrom, availability, brand.

Your task is to produce a JSON object called `carbon_input` that has this structure:

```
{
"materials": [
{
"name": <string or null>,
"weight": <float or null>,
"weight_source": <string>,
"emission_factor": <float or null>,
"emission_factor_source": <string or null>
}
],
"manufacturing_factor": {
"value": <float or null>,
"source": <string or null>
},
"transport": {
"origin": <string or null>,
"distance_km": <float or null>,
"mode": <string or null>,
"emission_factor_ton_km": <float or null>,
"source": <string or null>
},
"packaging": {
"weight": <float or null>,
"emission_factor": <float or null>,
"source": <string or null>
},
"product_weight": {
"value": <float or null>,
"source": <string or null>
}
}
```

### Critical formatting and output rules (READ CAREFULLY):
1. Always output a single valid JSON object ONLY. Do not include any explanations, notes, or markdown — only the JSON object.
2. For every key in the JSON schema above, if you cannot find or reasonably infer a value, set that key's value to `null`. Do NOT use other placeholders such as `"unknown"`, empty strings `""`, or numeric `0` unless 0 is a correct numeric value.
3. Numeric fields must be numbers (floats/ints) or `null`. String fields must be strings or `null`.
4. Do not add extra top-level keys beyond the schema shown. You may include multiple entries in the `"materials"` array, but each entry must follow the structure given. If you include the `"materials"` list but lack detail for some fields, set those fields to `null`.
5. You may use general world knowledge to estimate typical values (e.g., weight of running shoes ≈ 0.6 kg). When you do so, set the corresponding `<...>_source` to `"model-based estimate"` or `"retrieved from web"`. If you inferred a value from the provided product text (e.g., the product description states "500 g"), set the source to indicate that (e.g., `"source": "product description"`).
6. For emission factors and sources, prefer plausible references (DEFRA 2023, Ecoinvent v3.9, academic estimates). If you estimate, mark the source accordingly.
7. Use metric units (kg, km) and numeric values only.

Now transform the following product data into the required JSON format. For every field, if there is no information or you cannot infer a value, set it explicitly to `null`.

{product_json}
"""

def _construct_prompt(product: Dict[str, Any]) -> str:
    """
    Construct the final prompt by safely injecting the product JSON.

    We use replace(...) instead of format(...) because PROMPT_TEMPLATE contains many literal braces.
    """
    product_json = json.dumps(product, ensure_ascii=False)
    prompt = PROMPT_TEMPLATE.replace("{product_json}", product_json)
    return prompt

def _extract_first_json_block(text: str) -> Optional[str]:
    """
    Try to extract the first balanced JSON object from text.
    Returns the JSON string or None if not found.
    """
    if not text:
        return None

    # Clean common markdown fences
    # If the model returned a fenced code block like ```json { ... } ```
    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, flags=re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    # Find the first '{' and try to find the matching closing '}'
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    return None

def _safe_load_json(text: str) -> Any:
    # 1) direct load
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) extract first JSON block
    block = _extract_first_json_block(text)
    if block:
        try:
            return json.loads(block)
        except Exception:
            # Continue to next fallback
            pass

    # 3) replace single quotes with double quotes (very fragile, best-effort)
    # Only attempt if it looks like a dict with single quotes
    if re.search(r"^[\s\{'\[]", text) and ("'" in text and '"' not in text):
        try:
            fixed = text.replace("'", '"')
            return json.loads(fixed)
        except Exception:
            pass

    # Give a helpful error
    raise ValueError("Unable to parse JSON from LLM output.")

def transform_product(product: Dict[str, Any],
                      model: Optional[str] = "gemini-2.5-flash-lite",
                      temperature: float = 0.0,
                      max_tokens: int = 512,
                      llm_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    llm_kwargs = llm_kwargs or {}
    prompt = _construct_prompt(product)

    # Call the LLM
    raw_resp = call_llm(prompt, model=model, temperature=temperature, max_tokens=max_tokens, **llm_kwargs)
    if not raw_resp:
        raise ValueError("LLM returned an empty response")

    # Attempt to parse the JSON output
    try:
        parsed = _safe_load_json(raw_resp)
    except ValueError as e:
        # Attach the raw response for debugging
        raise ValueError(f"Failed to parse LLM JSON output: {e}\nLLM response:\n{raw_resp}") from e

    # Ensure top-level is a dict
    if not isinstance(parsed, dict):
        raise ValueError(f"Parsed JSON is not an object/dict. Got type {type(parsed)}. Response:\n{raw_resp}")

    return parsed

# Optional simple CLI for manual testing
if __name__ == "__main__":
    import sys
    example = {
        "platform": "ExampleShop",
        "url": "https://example.com/product/123",
        "image": None,
        "name": "Example Running Shoe",
        "price": "79.99 USD",
        "rating": 4.3,
        "shipper": "ExampleShipper",
        "seller": "ExampleSeller",
        "reviews": [],
        "shippingFrom": "China",
        "availability": "InStock",
        "brand": "ExampleBrand"
    }

    # Allow passing a small JSON on the command line
    if len(sys.argv) > 1:
        try:
            example = json.loads(sys.argv[1])
        except Exception as exc:
            print(f"Failed to parse CLI product JSON: {exc}")

    print("Calling LLM to transform example product...")
    try:
        out = transform_product(example, max_tokens=1024)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    except Exception as exc:
        print("Error:", exc)
