from flask import Blueprint, request, jsonify
import logging
import json

bp = Blueprint("product", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

# Import pipeline (new)
try:
    from server.pipeline import process_and_store_product
except Exception:
    logger.exception("Failed to import server.pipeline; pipeline functionality will be limited.")
    process_and_store_product = None


@bp.route('/product', methods=['POST'])
def receive_product():
    """Receive product data from extension and run full pipeline"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Basic product shape passed to pipeline
        product_data = {
            'platform': data.get('platform'),
            'url': data.get('url'),
            'image': data.get('image'),
            'name': data.get('name'),
            'price': data.get('price'),
            'rating': data.get('rating'),
            'shipper': data.get('shipper'),
            'seller': data.get('seller'),
            'reviews': data.get('reviews', []),
            'shippingFrom': data.get('shippingFrom'),
            'fulfilledBy': data.get('fulfilledBy'),
            'availability': data.get('availability'),
            'brand': data.get('brand'),
            'sku': data.get('sku') or data.get('id')
        }

        logger.info("Received product: %s", product_data.get('name'))

        if process_and_store_product is None:
            # Pipeline not available: just echo back
            return jsonify({
                'message': 'Pipeline not available on server. Received product data.',
                'data': product_data,
                'status': 'ok'
            }), 200

        # Run pipeline (synchronous). If you prefer async, adapt to background job / worker.
        result = process_and_store_product(product_data)

        # Build response compatible with frontend expectations
        product = result.get("product", {}) or {}
        recs = result.get("recommendations", []) or []

        # Helper to safely get recommendation fields by trying multiple keys
        def _rec_field(r, *keys):
            if not r:
                return ""
            for k in keys:
                v = r.get(k)
                if v:
                    return v
            return ""

        resp = {
            "status": result.get("status"),
            "messages": result.get("messages"),
            # keep product minimal
            "product": {
                "sku": product.get("sku"),
                "name": product.get("name"),
                "category": product.get("category"),
                "brand": product.get("brand"),
                "price": product.get("price"),
                "cf_value": product.get("cf_value"),
            }
        }

        # Primary C0Score required by frontend
        resp["C0Score"] = product.get("cf_value")

        # Fill link1..link5 and associated fields (populate with empty string/null when missing)
        for i in range(5):
            idx = i
            r = recs[idx] if idx < len(recs) else {}
            # URL (web_url/url)
            resp[f"link{i+1}"] = _rec_field(r, "web_url", "url")
            # C0 score for the recommendation
            resp[f"link{i+1}C0Score"] = r.get("cf_value")
            # Explanation: prefer _rec_debug (serialize), then explanation/reason fields
            expl = ""
            if r:
                debug = r.get("_rec_debug")
                if debug is not None:
                    try:
                        expl = json.dumps(debug, ensure_ascii=False)
                    except Exception:
                        expl = str(debug)
                else:
                    expl = _rec_field(r, "explanation", "reason", "_explanation") or ""
            resp[f"link{i+1}Explanation"] = expl
            # Image: image_url or image
            resp[f"link{i+1}Image"] = _rec_field(r, "image_url", "image")

        # Also return full recommendations array (backwards compatibility / debugging)
        resp["recommendations"] = recs

        return jsonify(resp), 200

    except Exception:
        logger.exception("Error in receive_product")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500
