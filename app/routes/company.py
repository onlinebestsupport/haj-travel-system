from flask import Blueprint, jsonify

company_bp = Blueprint('company', __name__)

@company_bp.route('/profile', methods=['GET'])
def get_company_profile():
    return jsonify({
        'success': True,
        'name': 'Alhudha Haj Travel',
        'tagline': 'Your Trusted Partner for Spiritual Journey to the Holy Land',
        'description': 'Experience the spiritual journey of a lifetime with our premium Haj and Umrah packages. 25+ years of trusted service guiding pilgrims to Makkah and Madinah.',
        'badge': 'Est. 1998',
        'features': [
            {'icon': 'fas fa-calendar-alt', 'title': '25+ Years', 'description': 'Experience in Haj & Umrah services'},
            {'icon': 'fas fa-users', 'title': '5000+', 'description': 'Happy Pilgrims Served'},
            {'icon': 'fas fa-hotel', 'title': 'Premium', 'description': 'Hotels near Haram'},
            {'icon': 'fas fa-bus', 'title': 'VIP Transport', 'description': 'Comfortable travel'}
        ]
    })
