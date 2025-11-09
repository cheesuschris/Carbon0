from flask import Flask, jsonify, request, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
import logging
import os

from routes.product import bp as product_bp

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MONGO_URI'] = 'mongodb+srv://cheesus:Coolchris1@cluster0.ovfnl.mongodb.net/Carbon0_database?retryWrites=true&w=majority&appName=Cluster0'
app.config['SECRET_KEY'] = os.urandom(16)
mongo = PyMongo(app)

CORS(app)

# Basic logging configuration for development
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


# Register blueprints
app.register_blueprint(product_bp)

@app.route('/')
def home():
    """Home route"""
    return jsonify({
        'message': 'Welcome to the Carbon0 Flask server',
        'status': 'running'
    })

@app.route('/cart/checkout', methods=['POST'])
def cart_checkout():
    try:
        data = request.get_json()
        amount = data.get('amount')
        if not mongo.db.TotalCarbonReduced.find_one():
            mongo.db.TotalCarbonReduced.insert_one({'Total': amount})
            return jsonify({
                'message': 'Carbon reduction tracked',
                'total': amount,
                'added': amount
            }), 201
        else:
            new_amount = mongo.db.TotalCarbonReduced.find_one().get('Total') + amount
            mongo.db.TotalCarbonReduced.update_one(
                {'_id': mongo.db.TotalCarbonReduced.find_one()['_id']},
                {'$set': {'Total': new_amount}}
            )
            return jsonify({
                'message': 'Carbon reduction updated',
                'Total': new_amount,
                'added': amount
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/carbon-total', methods=['GET'])
def get_carbon_total():
    try:
        doc = mongo.db.TotalCarbonReduced.find_one()
        if doc:
            total = doc.get('Total', 0)
            return jsonify({'total': total}), 200
        else:
            return jsonify({'total': 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config/gemini-key', methods=['GET'])
def get_gemini_key():
    """Get Gemini API key (for frontend use)"""
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key:
        return jsonify({
            'error': 'GEMINI_API_KEY environment variable not set'
        }), 500
    return jsonify({
        'key': gemini_key
    }), 200

@app.route('/cart', methods=['GET'])
def cart_page():
    """Carbon0 cart page for tracking alternatives and CO2 savings"""
    return send_from_directory('templates', 'cart.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

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
