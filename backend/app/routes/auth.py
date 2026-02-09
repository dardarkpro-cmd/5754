"""
Auth routes - POST /auth/login
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from app.models import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'login' not in data or 'pin' not in data:
        return jsonify({'error': 'missing_fields', 'message': 'login и pin обязательны'}), 400
    
    user = User.query.filter_by(login=data['login']).first()
    
    if not user or not check_password_hash(user.pin_hash, data['pin']):
        return jsonify({'error': 'invalid_credentials', 'message': 'Неверный логин или PIN'}), 401
    
    # Create JWT token with user info
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'role': user.role,
            'display_name': user.display_name
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'login': user.login,
            'role': user.role,
            'display_name': user.display_name,
            'language': user.language,
            'theme': user.theme
        }
    })
