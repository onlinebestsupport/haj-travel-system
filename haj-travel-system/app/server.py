from flask import Flask, send_from_directory
from flask_cors import CORS
from app.database import init_db
import os

app = Flask(__name__)
CORS(app)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'public')

@app.route('/')
def serve_index():
    return send_from_directory(PUBLIC_DIR, 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(PUBLIC_DIR, 'admin.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(PUBLIC_DIR, path)

@app.route('/api')
def api():
    return {
        "name": "Haj Travel System",
        "status": "active",
        "fields": 33
    }

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
