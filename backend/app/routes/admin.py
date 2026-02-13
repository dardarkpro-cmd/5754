"""
Admin routes - menu management, users CRUD, groups management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash
from app import db
from app.models import MenuItem, Inventory, Location, User, Group

bp = Blueprint('admin', __name__)

VALID_GROUP_TYPES = ('school', 'university', 'business')


def admin_required():
    """Check if current user is admin based on JWT claims"""
    claims = get_jwt()
    return claims.get('role') == 'admin'


def get_admin_user():
    """Get the current admin User object."""
    admin_id = get_jwt_identity()
    return User.query.get(admin_id)


# ==================== Menu ====================

@bp.route('/menu', methods=['GET'])
@jwt_required()
def get_admin_menu():
    """Get full menu for admin editing"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    items = MenuItem.query.all()
    
    result = []
    for item in items:
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
        inv = Inventory.query.filter_by(menu_item_id=item_id).first()
        if not inv:
            continue
        if 'qty' in item_data:
            inv.stock_qty = item_data['qty']
        if 'available' in item_data:
            inv.is_available = item_data['available']
        updated.append(item_id)
    
    db.session.commit()
    return get_admin_menu()


# ==================== Users CRUD ====================

def user_to_dict(user):
    """Serialize user with group info."""
    d = {
        'id': user.id,
        'login': user.login,
        'role': user.role,
        'display_name': user.display_name or '',
        'org_id': user.org_id,
        'group_id': user.group_id,
        'group': None
    }
    if user.group_id and user.group:
        d['group'] = {
            'id': user.group.id,
            'name': user.group.name,
            'type': user.group.type
        }
    return d


@bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users for admin's org"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    admin = get_admin_user()
    users = User.query.filter_by(org_id=admin.org_id).all()
    return jsonify({'users': [user_to_dict(u) for u in users]})


@bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user in admin's org"""
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
    
    if User.query.filter_by(login=login).first():
        return jsonify({'error': 'login_exists', 'message': 'Login already exists'}), 400
    
    if role not in ('user', 'cook', 'admin'):
        role = 'user'
    
    admin = get_admin_user()
    
    new_user = User(
        org_id=admin.org_id,
        login=login,
        pin_hash=generate_password_hash(pin),
        role=role,
        display_name=display_name
    )
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'user': user_to_dict(new_user)}), 201


@bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user. Login cannot be changed."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'not_found', 'message': 'User not found'}), 404
    
    # Ensure same org
    admin = get_admin_user()
    if user.org_id != admin.org_id:
        return jsonify({'error': 'forbidden', 'message': 'Cannot edit user from another org'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing_data', 'message': 'Request body required'}), 400
    
    if 'role' in data and data['role'] in ('user', 'cook', 'admin'):
        user.role = data['role']
    if 'display_name' in data:
        user.display_name = data['display_name']
    if 'pin' in data and data['pin']:
        user.pin_hash = generate_password_hash(data['pin'])
    
    db.session.commit()
    return jsonify({'user': user_to_dict(user)})


@bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user. Cannot delete self or last admin."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403
    
    current_user_id = get_jwt_identity()
    if user_id == current_user_id:
        return jsonify({'error': 'cannot_delete_self', 'message': 'Cannot delete yourself'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'not_found', 'message': 'User not found'}), 404
    
    admin = get_admin_user()
    if user.org_id != admin.org_id:
        return jsonify({'error': 'forbidden', 'message': 'Cannot delete user from another org'}), 403
    
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin', org_id=admin.org_id).count()
        if admin_count <= 1:
            return jsonify({'error': 'last_admin', 'message': 'Cannot delete the last admin'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted'})


# ==================== Groups ====================

@bp.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    """List all groups for admin's organization."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403

    admin = get_admin_user()
    groups = Group.query.filter_by(org_id=admin.org_id).order_by(Group.name).all()

    result = []
    for g in groups:
        result.append({
            'id': g.id,
            'name': g.name,
            'type': g.type,
            'user_count': g.users.count(),
            'created_at': g.created_at.isoformat() if g.created_at else None
        })

    return jsonify({'groups': result})


@bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    """Create a new group in admin's organization."""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing_data', 'message': 'Request body required'}), 400

    name = (data.get('name') or '').strip()
    gtype = (data.get('type') or '').strip().lower()

    if not name:
        return jsonify({'error': 'missing_name', 'message': 'Group name is required'}), 400
    if gtype not in VALID_GROUP_TYPES:
        return jsonify({
            'error': 'invalid_type',
            'message': f'type must be one of: {", ".join(VALID_GROUP_TYPES)}'
        }), 400

    admin = get_admin_user()

    # Check uniqueness within org
    existing = Group.query.filter_by(org_id=admin.org_id, name=name).first()
    if existing:
        return jsonify({'error': 'group_exists', 'message': 'Group with this name already exists'}), 400

    new_group = Group(org_id=admin.org_id, name=name, type=gtype)
    db.session.add(new_group)
    db.session.commit()

    return jsonify({
        'group': {
            'id': new_group.id,
            'name': new_group.name,
            'type': new_group.type,
            'user_count': 0
        }
    }), 201


@bp.route('/users/<user_id>/group', methods=['PUT'])
@jwt_required()
def assign_group(user_id):
    """Assign or remove a group for a user. body: {"group_id": "<id>"} or {"group_id": null}"""
    if not admin_required():
        return jsonify({'error': 'forbidden', 'message': 'Admin access required'}), 403

    admin = get_admin_user()

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'not_found', 'message': 'User not found'}), 404
    if user.org_id != admin.org_id:
        return jsonify({'error': 'forbidden', 'message': 'Cannot modify user from another org'}), 403

    data = request.get_json()
    if data is None:
        return jsonify({'error': 'missing_data', 'message': 'Request body required'}), 400

    group_id = data.get('group_id')

    if group_id is None:
        # Remove group
        user.group_id = None
    else:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'error': 'group_not_found', 'message': 'Group not found'}), 404
        if group.org_id != admin.org_id:
            return jsonify({'error': 'forbidden', 'message': 'Cannot assign group from another org'}), 403
        user.group_id = group_id

    db.session.commit()
    return jsonify({'user': user_to_dict(user)})
