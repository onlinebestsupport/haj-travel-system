from flask import Blueprint

travelers_bp = Blueprint('travelers', __name__)

@travelers_bp.route('/')
def get_travelers():
    return {"message": "Travelers API"}
