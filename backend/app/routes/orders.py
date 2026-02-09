"""
Orders routes - POST /orders, POST /payments/fake, GET /orders/{id}
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app import db
from app.models import Order, OrderItem, MenuItem, Inventory, Receipt, User, Location

bp = Blueprint('orders', __name__)


@bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not data or 'items' not in data or not data['items']:
        return jsonify({'error': 'missing_items', 'message': 'items обязательны'}), 400
    
    # Get location
    location = Location.query.filter_by(org_id=user.org_id).first()
    if not location:
        return jsonify({'error': 'location_not_found'}), 404
    
    # Parse scheduled_for or default to now + 1h
    scheduled_for = data.get('scheduled_for')
    if scheduled_for:
        scheduled_for = datetime.fromisoformat(scheduled_for.replace('Z', '+00:00'))
    else:
        scheduled_for = datetime.utcnow() + timedelta(hours=1)
    
    # Validate: max +3 hours
    if scheduled_for > datetime.utcnow() + timedelta(hours=3):
        return jsonify({
            'error': 'scheduled_time_invalid',
            'message': 'Время должно быть не более +3 часов'
        }), 400
    
    # Create order
    order = Order(
        user_id=user_id,
        location_id=location.id,
        status='CREATED',
        scheduled_for=scheduled_for,
        total=0
    )
    db.session.add(order)
    
    # Add items
    total = 0
    order_items_response = []
    
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item:
            db.session.rollback()
            return jsonify({
                'error': 'item_not_found',
                'message': f"Блюдо {item_data['menu_item_id']} не найдено"
            }), 400
        
        # Check availability
        inv = Inventory.query.filter_by(
            location_id=location.id,
            menu_item_id=menu_item.id
        ).first()
        
        if not inv or not inv.is_available:
            db.session.rollback()
            return jsonify({
                'error': 'item_unavailable',
                'message': f"Блюдо '{menu_item.name_ru}' недоступно",
                'item_id': menu_item.id
            }), 400
        
        qty = item_data.get('qty', 1)
        subtotal = menu_item.base_price * qty
        total += subtotal
        
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            qty=qty,
            unit_price=menu_item.base_price,
            comment=item_data.get('comment')
        )
        db.session.add(order_item)
        
        order_items_response.append({
            'menu_item_id': menu_item.id,
            'name': menu_item.name_ru,
            'qty': qty,
            'unit_price': menu_item.base_price,
            'subtotal': subtotal
        })
    
    order.total = total
    db.session.commit()
    
    return jsonify({
        'order_id': order.id,
        'status': order.status,
        'total': total,
        'scheduled_for': order.scheduled_for.isoformat(),
        'items': order_items_response,
        'created_at': order.created_at.isoformat()
    }), 201


@bp.route('/payments/fake', methods=['POST'])
@jwt_required()
def fake_payment():
    data = request.get_json()
    
    if not data or 'order_id' not in data:
        return jsonify({'error': 'missing_order_id'}), 400
    
    order = Order.query.get(data['order_id'])
    if not order:
        return jsonify({'error': 'order_not_found'}), 404
    
    if order.status != 'CREATED':
        return jsonify({
            'error': 'invalid_order_status',
            'message': 'Заказ уже оплачен или отменён'
        }), 400
    
    # Update status
    order.status = 'PAID'
    
    # Create receipt
    items_data = []
    for item in order.items:
        items_data.append({
            'name': item.menu_item.name_ru,
            'qty': item.qty,
            'unit_price': item.unit_price,
            'subtotal': item.qty * item.unit_price
        })
    
    receipt = Receipt(
        order_id=order.id,
        receipt_data={
            'items': items_data,
            'total': order.total,
            'paid_at': datetime.utcnow().isoformat()
        }
    )
    db.session.add(receipt)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'status': 'PAID',
        'receipt': {
            'id': receipt.id,
            'order_id': order.id,
            'items': items_data,
            'total': order.total,
            'paid_at': receipt.receipt_data['paid_at']
        }
    })


@bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'order_not_found'}), 404
    
    # Lazy-expire check
    if order.status == 'READY' and order.reservation:
        if datetime.utcnow() > order.reservation.hold_until:
            order.status = 'EXPIRED'
            order.reservation.released_at = datetime.utcnow()
            order.reservation.cell.status = 'FREE'
            db.session.commit()
    
    # Get active token
    active_token = None
    for token in order.tokens:
        if token.used_at is None:
            active_token = token
            break
    
    response = {
        'id': order.id,
        'status': order.status,
        'scheduled_for': order.scheduled_for.isoformat(),
        'total': order.total,
        'items': [{
            'name': item.menu_item.name_ru,
            'qty': item.qty,
            'unit_price': item.unit_price
        } for item in order.items]
    }
    
    if order.reservation and active_token:
        response['pickup'] = {
            'cell_code': order.reservation.cell.code,
            'qr_token': active_token.qr_token,
            'pin_code': active_token.pin_code,
            'token_expires_at': active_token.token_expires_at.isoformat(),
            'pickup_deadline_at': order.reservation.hold_until.isoformat(),
            'token_valid': datetime.utcnow() < active_token.token_expires_at
        }
    
    return jsonify(response)
