"""
Pickup routes - POST /pickup/claim
Implements all invariants: INV-1 to INV-4
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import PickupToken, Order, LockerReservation

bp = Blueprint('pickup', __name__)


@bp.route('/pickup/claim', methods=['POST'])
def claim():
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'invalid_request'}), 400
    
    token = None
    
    # Find token by QR or PIN
    if 'qr_token' in data:
        token = PickupToken.query.filter_by(qr_token=data['qr_token']).first()
    elif 'pin_code' in data and 'order_id' in data:
        token = PickupToken.query.filter_by(
            order_id=data['order_id'],
            pin_code=data['pin_code']
        ).order_by(PickupToken.created_at.desc()).first()
    else:
        return jsonify({
            'error': 'missing_fields',
            'message': 'Нужен qr_token или (order_id + pin_code)'
        }), 400
    
    # INV-4: INVALID_TOKEN
    if not token:
        return jsonify({
            'error': 'INVALID_TOKEN',
            'message': 'Неверный код'
        }), 404
    
    order = token.order
    reservation = LockerReservation.query.filter_by(order_id=order.id).first()
    
    # INV-2: ALREADY_PICKED_UP (idempotent - return 200)
    if order.status == 'PICKED_UP':
        cell_code = reservation.cell.code if reservation else 'N/A'
        return jsonify({
            'success': True,
            'order_id': order.id,
            'cell_code': cell_code,
            'message': 'Заказ уже получен'
        }), 200
    
    # Lazy-expire: check cell hold
    if reservation and datetime.utcnow() > reservation.hold_until:
        order.status = 'EXPIRED'
        reservation.released_at = datetime.utcnow()
        reservation.cell.status = 'FREE'
        db.session.commit()
        return jsonify({
            'error': 'ORDER_EXPIRED',
            'message': 'Время хранения заказа истекло'
        }), 400
    
    # INV-4: CELL_RELEASED
    if reservation and reservation.released_at and order.status != 'PICKED_UP':
        return jsonify({
            'error': 'CELL_RELEASED',
            'message': 'Ячейка уже освобождена'
        }), 400
    
    # INV-4: TOKEN_ALREADY_USED
    if token.used_at is not None:
        return jsonify({
            'error': 'TOKEN_ALREADY_USED',
            'message': 'Токен уже использован'
        }), 400
    
    # INV-4: TOKEN_EXPIRED
    if datetime.utcnow() > token.token_expires_at:
        return jsonify({
            'error': 'TOKEN_EXPIRED',
            'message': 'Токен истёк, обратитесь к повару для перевыпуска'
        }), 400
    
    # All checks passed - claim the order
    token.used_at = datetime.utcnow()
    order.status = 'PICKED_UP'
    
    if reservation:
        reservation.released_at = datetime.utcnow()
        reservation.cell.status = 'FREE'
        cell_code = reservation.cell.code
    else:
        cell_code = 'N/A'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'cell_code': cell_code,
        'message': f'Ячейка {cell_code} открыта. Заберите заказ.'
    })
