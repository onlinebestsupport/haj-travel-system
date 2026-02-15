from flask import Blueprint

uploads_bp = Blueprint('uploads', __name__)

@uploads_bp.route('/')
def upload_file():
    return {"message": "Upload API"}
