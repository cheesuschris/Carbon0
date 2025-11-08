from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    """Home route"""
    return jsonify({
        'message': 'Welcome to the Flask server',
        'status': 'running'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

