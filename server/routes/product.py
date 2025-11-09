from flask import Blueprint, request, jsonify, current_app
import logging

bp = Blueprint("product", __name__, url_prefix="/api")

logger = logging.getLogger(__name__)

# Import pipeline (new)
try:
    from server.pipeline import process_and_store_product
except Exception as e:
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

        # Return structured result to client (trim heavy fields)
        response = {
            "status": result.get("status"),
            "messages": result.get("messages"),
            "product": {
                "sku": result.get("product", {}).get("sku"),
                "name": result.get("product", {}).get("name"),
                "category": result.get("product", {}).get("category"),
                "brand": result.get("product", {}).get("brand"),
                "price": result.get("product", {}).get("price"),
                "cf_value": result.get("product", {}).get("cf_value"),
            },
            "recommendations": [
                {
                    "sku": r.get("sku"),
                    "name": r.get("name"),
                    "category": r.get("category"),
                    "brand": r.get("brand"),
                    "price": r.get("price"),
                    "cf_value": r.get("cf_value"),
                    "_rec_score": r.get("_rec_score"),
                    "_rec_debug": r.get("_rec_debug")
                }
                for r in result.get("recommendations", [])
            ]
        }
        return jsonify(response), 200

    except Exception as e:
        logger.exception("Error in receive_product")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500
