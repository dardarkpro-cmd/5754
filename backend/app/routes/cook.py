"""
Cook routes - GET /cook/orders/queue, POST /cook/orders/{id}/ready
"""
import secrets
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime, timedelta
from app import db
from app.models import Order, LockerCell, LockerReservation, PickupToken, Location

bp = Blueprint('cook', __name__)


def generate_token():
    return f"qr-{secrets.token_hex(16)}"


def generate_pin():
    return str(random.randint(100000, 999999))


@bp.route('/orders/queue', methods=['GET'])
@jwt_required()
def get_queue():
    claims = get_jwt()
    if claims.get('role') not in ['cook', 'admin']:
        return jsonify({'error': 'forbidden', 'message': 'Только для повара'}), 403
    
    # Get orders in PAID or IN_KITCHEN status
    orders = Order.query.filter(
        Order.status.in_(['PAID', 'IN_KITCHEN'])
    ).order_by(Order.scheduled_for.asc()).all()
    
    return jsonify({
        'orders': [{
            'id': order.id,
            'status': order.status,
            'scheduled_for': order.scheduled_for.isoformat(),
            'total': order.total,
            'items': [{
                'name': item.menu_item.name_ru,
                'qty': item.qty
            } for item in order.items],
            'user': {
                'display_name': order.user.display_name
            }
        } for order in orders]
    })


@bp.route('/orders/<order_id>/ready', methods=['POST'])
@jwt_required()
def mark_ready(order_id):
    claims = get_jwt()
    if claims.get('role') not in ['cook', 'admin']:
        return jsonify({'error': 'forbidden'}), 403
    
    data = request.get_json(force=True, silent=True) or {}
    cell_code = data.get('cell_code')
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'order_not_found'}), 404
    
    if order.status not in ['PAID', 'IN_KITCHEN']:
        return jsonify({
            'error': 'invalid_order_status',
            'message': 'Заказ должен быть в статусе PAID или IN_KITCHEN'
        }), 400
    
    # Find cell
    if cell_code:
        cell = LockerCell.query.filter_by(
            location_id=order.location_id,
            code=cell_code
        ).first()
    else:
        # Auto-assign first FREE cell
        cell = LockerCell.query.filter_by(
            location_id=order.location_id,
            status='FREE'
        ).first()
    
    if not cell:
        return jsonify({
            'error': 'no_free_cells',
            'message': 'Нет свободных ячеек'
        }), 400
    
    if cell.status != 'FREE':
        return jsonify({
            'error': 'cell_occupied',
            'message': f'Ячейка {cell.code} уже занята'
        }), 400
    
    # Revoke existing tokens (INV-1)
    PickupToken.query.filter_by(order_id=order.id).filter(
        PickupToken.used_at.is_(None)
    ).update({'used_at': datetime.utcnow()})
    
    # Create reservation
    hold_until = datetime.utcnow() + timedelta(minutes=60)
    
    # Check location closing time
    location = Location.query.get(order.location_id)
    if location and location.closing_time:
        closing_dt = datetime.combine(datetime.utcnow().date(), location.closing_time)
        if closing_dt < hold_until:
            hold_until = closing_dt + timedelta(minutes=15)
    
    reservation = LockerReservation(
        order_id=order.id,
        cell_id=cell.id,
        hold_until=hold_until
    )
    db.session.add(reservation)
    
    # Update cell status
    cell.status = 'OCCUPIED'
    
    # Create token
    token = PickupToken(
        order_id=order.id,
        qr_token=generate_token(),
        pin_code=generate_pin(),
        token_expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.session.add(token)
    
    # Update order
    order.status = 'READY'
    order.pickup_deadline_at = hold_until
    
    db.session.commit()
    
    return jsonify({
        'order_id': order.id,
        'status': 'READY',
        'pickup': {
            'cell_code': cell.code,
            'qr_token': token.qr_token,
            'pin_code': token.pin_code,
            'token_expires_at': token.token_expires_at.isoformat(),
            'pickup_deadline_at': hold_until.isoformat()
        }
    })
