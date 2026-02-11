from app import create_app
from app.database import init_db
import os

app = create_app()

@app.route('/')
def home():
    return {"message": "Haj Travel System API"}

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
