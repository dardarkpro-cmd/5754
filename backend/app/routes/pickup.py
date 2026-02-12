"""
Pickup routes - POST /pickup/claim
MVP: claim order by order_id + pickup_code
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Order, LockerReservation

bp = Blueprint('pickup', __name__)


@bp.route('/pickup/claim', methods=['POST'])
def claim():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'invalid_request'}), 400
    
    order_id = data.get('order_id')
    pickup_code = data.get('pickup_code')
    
    if not order_id or not pickup_code:
        return jsonify({
            'error': 'missing_fields',
            'message': 'order_id и pickup_code обязательны'
        }), 400
    
    # Find order
    order = Order.query.get(order_id)
    if not order:
        return jsonify({
            'error': 'order_not_found',
            'message': 'Заказ не найден'
        }), 404
    
    # Already picked up (idempotent)
    if order.status == 'PICKED_UP':
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Заказ уже получен'
        }), 200
    
    # Must be READY
    if order.status != 'READY':
        return jsonify({
            'error': 'order_not_ready',
            'message': f'Заказ в статусе {order.status}, ожидается READY'
        }), 400
    
    # Verify pickup code
    if order.pickup_code != pickup_code:
        return jsonify({
            'error': 'invalid_pickup_code',
            'message': 'Неверный код выдачи'
        }), 400
    
    # All checks passed - claim the order
    order.status = 'PICKED_UP'
    order.picked_up_at = datetime.utcnow()
    
    # Release locker cell if reserved
    reservation = LockerReservation.query.filter_by(order_id=order.id).first()
    cell_code = None
    if reservation and not reservation.released_at:
        reservation.released_at = datetime.utcnow()
        reservation.cell.status = 'FREE'
        cell_code = reservation.cell.code
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'message': 'Заказ выдан успешно!',
        'cell_code': cell_code
    })
