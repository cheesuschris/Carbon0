from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

from routes.product import bp as product_bp

app = Flask(__name__)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
