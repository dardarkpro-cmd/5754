"""
Admin routes - GET/PUT /admin/menu
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models import MenuItem, Inventory, Location, User

bp = Blueprint('admin', __name__)


def admin_required():
    """Check if current user is admin based on JWT claims"""
    claims = get_jwt()
    return claims.get('role') == 'admin'


@bp.route('/menu', methods=['GET'])
@jwt_required()
def get_admin_menu():
    """Get full menu for admin editing"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    # Get all menu items (admin sees all orgs for MVP, or filter by org if needed)
    items = MenuItem.query.all()
    
    result = []
    for item in items:
        # Get inventory for first location
        inv = Inventory.query.filter_by(menu_item_id=item.id).first()
        
        result.append({
            'id': item.id,
            'name_kz': item.name_kz,
            'name_ru': item.name_ru,
            'name_en': item.name_en or '',
            'price': item.base_price,
            'category': item.category,
            'qty': inv.stock_qty if inv else 0,
            'available': inv.is_available if inv else False
        })
    
    return jsonify({'items': result})


@bp.route('/menu', methods=['PUT'])
@jwt_required()
def update_admin_menu():
    """Update menu items (qty, available)"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'error': 'missing_items', 'message': 'items array required'}), 400
    
    updated = []
    for item_data in data['items']:
        item_id = item_data.get('id')
        if not item_id:
            continue
        
        # Find inventory record
        inv = Inventory.query.filter_by(menu_item_id=item_id).first()
        if not inv:
            continue
        
        # Update fields if provided
        if 'qty' in item_data:
            inv.stock_qty = item_data['qty']
        if 'available' in item_data:
            inv.is_available = item_data['available']
        
        updated.append(item_id)
    
    db.session.commit()
    
    # Return updated menu
    return get_admin_menu()


# ==================== Users CRUD ====================

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'login': user.login,
            'role': user.role,
            'display_name': user.display_name or '',
            'org_id': user.org_id
        })
    
    return jsonify({'users': result})


@bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user (admin only)"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing_data', 'message': 'Request body required'}), 400
    
    login = data.get('login')
    pin = data.get('pin')
    role = data.get('role', 'user')
    display_name = data.get('display_name', '')
    
    if not login or not pin:
        return jsonify({'error': 'missing_fields', 'message': 'login and pin are required'}), 400
    
    # Check unique login
    existing = User.query.filter_by(login=login).first()
    if existing:
        return jsonify({'error': 'login_exists', 'message': 'Login already exists'}), 400
    
    # Validate role
    valid_roles = ['user', 'cook', 'admin']
    if role not in valid_roles:
        role = 'user'
    
    # Get org_id from current admin user
    from flask_jwt_extended import get_jwt_identity
    admin_id = get_jwt_identity()
    admin_user = User.query.get(admin_id)
    org_id = admin_user.org_id if admin_user else 'org-1'
    
    # Hash pin
    from werkzeug.security import generate_password_hash
    pin_hash = generate_password_hash(pin)
    
    new_user = User(
        org_id=org_id,
        login=login,
        pin_hash=pin_hash,
        role=role,
        display_name=display_name
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'user': {
            'id': new_user.id,
            'login': new_user.login,
            'role': new_user.role,
            'display_name': new_user.display_name or '',
            'org_id': new_user.org_id
        }
    }), 201


@bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user (admin only). Login cannot be changed."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'not_found', 'message': 'User not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing_data', 'message': 'Request body required'}), 400
    
    # Update role if provided
    if 'role' in data:
        valid_roles = ['user', 'cook', 'admin']
        if data['role'] in valid_roles:
            user.role = data['role']
    
    # Update display_name if provided
    if 'display_name' in data:
        user.display_name = data['display_name']
    
    # Update pin if provided (non-empty)
    if 'pin' in data and data['pin']:
        from werkzeug.security import generate_password_hash
        user.pin_hash = generate_password_hash(data['pin'])
    
    db.session.commit()
    
    return jsonify({
        'user': {
            'id': user.id,
            'login': user.login,
            'role': user.role,
            'display_name': user.display_name or '',
            'org_id': user.org_id
        }
    })


@bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user (admin only). Cannot delete self or last admin."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    from flask_jwt_extended import get_jwt_identity
    current_user_id = get_jwt_identity()
    
    # Cannot delete self
    if user_id == current_user_id:
        return jsonify({'error': 'cannot_delete_self', 'message': 'Cannot delete yourself'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'not_found', 'message': 'User not found'}), 404
    
    # Cannot delete last admin
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            return jsonify({'error': 'last_admin', 'message': 'Cannot delete the last admin'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted'})

