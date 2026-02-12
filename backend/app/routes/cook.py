"""
Cook routes - GET /cook/orders/queue, POST /cook/orders/{id}/ready
             GET /cook/daily-menu, PUT /cook/daily-menu
"""
import secrets
import random
from datetime import datetime, date as date_type, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models import (
    Order, LockerCell, LockerReservation, Location,
    MenuItem, DailyMenu, DailyMenuItem
)

bp = Blueprint('cook', __name__)


# ==================== Daily Menu ====================

@bp.route('/daily-menu', methods=['GET'])
@jwt_required()
def get_daily_menu():
    claims = get_jwt()
    if claims.get('role') not in ['cook', 'admin']:
        return jsonify({'error': 'forbidden'}), 403
    
    location_id = request.args.get('location_id')
    date_str = request.args.get('date')
    meal_slot = request.args.get('meal_slot', 'lunch')
    
    if not location_id:
        return jsonify({'error': 'missing_location_id'}), 400
    
    if date_str:
        try:
            menu_date = date_type.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'invalid_date', 'message': 'Use YYYY-MM-DD'}), 400
    else:
        menu_date = date_type.today()
    
    daily_menu = DailyMenu.query.filter_by(
        location_id=location_id,
        menu_date=menu_date,
        meal_slot=meal_slot
    ).first()
    
    if not daily_menu:
        return jsonify({
            'daily_menu': None,
            'location_id': location_id,
            'date': menu_date.isoformat(),
            'meal_slot': meal_slot,
            'items': []
        })
    
    items = []
    for dmi in daily_menu.items:
        mi = dmi.menu_item
        items.append({
            'menu_item_id': mi.id,
            'name_ru': mi.name_ru,
            'name_kz': mi.name_kz,
            'category': mi.category,
            'base_price': mi.base_price,
            'stock_qty': dmi.stock_qty,
            'is_available': dmi.is_available
        })
    
    return jsonify({
        'daily_menu': {
            'id': daily_menu.id,
            'created_by': daily_menu.created_by,
            'created_at': daily_menu.created_at.isoformat() if daily_menu.created_at else None
        },
        'location_id': location_id,
        'date': menu_date.isoformat(),
        'meal_slot': meal_slot,
        'items': items
    })


@bp.route('/daily-menu', methods=['PUT'])
@jwt_required()
def save_daily_menu():
    claims = get_jwt()
    user_id = get_jwt_identity()
    if claims.get('role') not in ['cook', 'admin']:
        return jsonify({'error': 'forbidden'}), 403
    
    data = request.get_json(force=True, silent=True) or {}
    location_id = data.get('location_id')
    date_str = data.get('menu_date')
    meal_slot = data.get('meal_slot', 'lunch')
    items_data = data.get('items', [])
    
    if not location_id or not date_str:
        return jsonify({'error': 'missing_fields', 'message': 'location_id and menu_date required'}), 400
    
    try:
        menu_date = date_type.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'invalid_date'}), 400
    
    # Verify location exists
    location = Location.query.get(location_id)
    if not location:
        return jsonify({'error': 'location_not_found'}), 404
    
    # Upsert DailyMenu
    daily_menu = DailyMenu.query.filter_by(
        location_id=location_id,
        menu_date=menu_date,
        meal_slot=meal_slot
    ).first()
    
    if not daily_menu:
        daily_menu = DailyMenu(
            location_id=location_id,
            menu_date=menu_date,
            meal_slot=meal_slot,
            created_by=user_id
        )
        db.session.add(daily_menu)
        db.session.flush()  # get id
    
    # Build set of incoming menu_item_ids
    incoming_ids = set()
    for item_data in items_data:
        mid = item_data.get('menu_item_id')
        if mid:
            incoming_ids.add(mid)
    
    # Delete items not in new list
    existing_items = {dmi.menu_item_id: dmi for dmi in daily_menu.items}
    for mid, dmi in existing_items.items():
        if mid not in incoming_ids:
            db.session.delete(dmi)
    
    # Add or update items
    for item_data in items_data:
        mid = item_data.get('menu_item_id')
        if not mid:
            continue
        
        if mid in existing_items:
            # Update
            dmi = existing_items[mid]
            dmi.stock_qty = item_data.get('stock_qty')
            dmi.is_available = item_data.get('is_available', True)
        else:
            # Add new
            dmi = DailyMenuItem(
                daily_menu_id=daily_menu.id,
                menu_item_id=mid,
                stock_qty=item_data.get('stock_qty'),
                is_available=item_data.get('is_available', True)
            )
            db.session.add(dmi)
    
    db.session.commit()
    
    return jsonify({
        'ok': True,
        'daily_menu_id': daily_menu.id,
        'items_count': len(items_data)
    })


# ==================== Order Queue ====================

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
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'order_not_found'}), 404
    
    if order.status not in ['PAID', 'IN_KITCHEN']:
        return jsonify({
            'error': 'invalid_order_status',
            'message': 'Заказ должен быть в статусе PAID или IN_KITCHEN'
        }), 400
    
    # Generate 6-digit pickup code if not already set
    if not order.pickup_code:
        order.pickup_code = f"{random.randint(0, 999999):06d}"
    
    # Update order status
    order.status = 'READY'
    order.ready_at = datetime.utcnow()
    
    # Try to assign a locker cell (optional, best-effort)
    data = request.get_json(force=True, silent=True) or {}
    cell_code_req = data.get('cell_code')
    cell_info = None
    
    if cell_code_req:
        cell = LockerCell.query.filter_by(
            location_id=order.location_id,
            code=cell_code_req
        ).first()
    else:
        cell = LockerCell.query.filter_by(
            location_id=order.location_id,
            status='FREE'
        ).first()
    
    if cell and cell.status == 'FREE':
        hold_until = datetime.utcnow() + timedelta(minutes=60)
        
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
        cell.status = 'OCCUPIED'
        order.pickup_deadline_at = hold_until
        cell_info = cell.code
    
    db.session.commit()
    
    response = {
        'order_id': order.id,
        'status': 'READY',
        'pickup_code': order.pickup_code
    }
    if cell_info:
        response['cell_code'] = cell_info
    
    return jsonify(response)
