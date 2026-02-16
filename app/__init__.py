from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    from app.routes.travelers import travelers_bp
    from app.routes.uploads import uploads_bp
    
    app.register_blueprint(travelers_bp, url_prefix='/api/travelers')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    
    return app
