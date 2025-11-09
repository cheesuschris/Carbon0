from flask import Flask, jsonify, request, send_from_directory
from flask_pymongo import PyMongo
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from server.routes.product import bp as product_bp
from server.database import init_db

app = Flask(__name__, static_folder='static', template_folder='templates')

MONGO_URI = os.getenv('MONGO_URI')
app.config['MONGO_URI'] = MONGO_URI

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = os.urandom(16).hex()
app.config['SECRET_KEY'] = SECRET_KEY

DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'
PORT = int(os.environ.get('PORT', 5000))

mongo = PyMongo(app)
CORS(app)

app.register_blueprint(product_bp)

@app.route('/')
def home():
    """Home route - serve index.html"""
    return send_from_directory('templates', 'index.html')

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
            print(new_amount)
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

@app.route('/api/final-output/<filename>')
def get_final_output(filename):
    """Serve final_output JSON files"""
    import json
    import os
    from flask import abort
    
    # Security: Only allow final_output_*.json files
    if not filename.startswith('final_output_') or not filename.endswith('.json'):
        abort(400, description="Invalid filename")
    
    # Construct file path
    base_dir = os.path.dirname(__file__)
    filepath = os.path.join(base_dir, filename)
    
    if not os.path.exists(filepath):
        abort(404, description="File not found")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)