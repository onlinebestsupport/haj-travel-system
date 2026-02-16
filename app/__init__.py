from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Simple health check - NO DATABASE, NO COMPLEX CODE
@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def home():
    return jsonify({"message": "Alhudha Haj Travel API"})

# Import routes AFTER app is created
from app.routes import travelers, uploads
app.register_blueprint(travelers.travelers_bp, url_prefix='/api/travelers')
app.register_blueprint(uploads.uploads_bp, url_prefix='/api/uploads')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
