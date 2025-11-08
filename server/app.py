from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Home route"""
    return jsonify({
        'message': 'Welcome to the Carbon0 Flask server',
        'status': 'running'
    })

@app.route('/api/product', methods=['POST'])
def receive_product():
    """Receive product data from extension"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
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
            'brand': data.get('brand')
        }
        
        print(f"\n{'='*60}")
        print(f"Received product data: {product_data['name']} from {product_data['platform']}")
        print(f"{'='*60}")
        import json
        print(json.dumps(product_data, indent=2, ensure_ascii=False))
        print(f"{'='*60}\n")
        
        return jsonify({
            'message': 'Product data received successfully',
            'data': product_data,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
