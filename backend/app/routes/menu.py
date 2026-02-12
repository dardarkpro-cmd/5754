"""
Menu routes - GET /menu, GET /catalog
"""
from datetime import datetime, date as date_type
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import MenuItem, Inventory, Location, User, DailyMenu, DailyMenuItem

bp = Blueprint('menu', __name__)


@bp.route('/menu', methods=['GET'])
@jwt_required()
def get_menu():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'user_not_found'}), 404
    
    # Determine location
    location_id = request.args.get('location_id')
    if location_id:
        location = Location.query.get(location_id)
    else:
        location = Location.query.filter_by(org_id=user.org_id).first()
    
    if not location:
        return jsonify({'error': 'location_not_found'}), 404
    
    if location.is_closed_manual:
        return jsonify({
            'error': 'location_closed',
            'message': 'Столовая сейчас закрыта'
        }), 403
    
    # Determine date
    date_str = request.args.get('date')
    if date_str:
        try:
            menu_date = date_type.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'invalid_date', 'message': 'Use YYYY-MM-DD'}), 400
    else:
        menu_date = date_type.today()
    
    meal_slot = request.args.get('meal_slot', 'lunch')
    
    # Look up DailyMenu
    daily_menu = DailyMenu.query.filter_by(
        location_id=location.id,
        menu_date=menu_date,
        meal_slot=meal_slot
    ).first()
    
    items = []
    if daily_menu:
        for dmi in daily_menu.items:
            item = dmi.menu_item
            items.append({
                'id': item.id,
                'name': item.name_ru,
                'name_kz': item.name_kz,
                'name_ru': item.name_ru,
                'category': item.category,
                'price': item.base_price,
                'is_available': dmi.is_available,
                'stock_qty': dmi.stock_qty,
                'image_url': item.image_url,
                'nutrition': {
                    'calories': item.calories_100g,
                    'protein': item.protein_100g,
                    'fat': item.fat_100g,
                    'carbs': item.carbs_100g
                }
            })
    
    return jsonify({
        'location': {
            'id': location.id,
            'name': location.name,
            'is_closed': location.is_closed_manual
        },
        'meal_slot': meal_slot,
        'date': menu_date.isoformat(),
        'has_daily_menu': daily_menu is not None,
        'items': items
    })


@bp.route('/catalog', methods=['GET'])
@jwt_required()
def get_catalog():
    """Return all menu items from the org catalog (for cook daily-menu picker)."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'user_not_found'}), 404
    
    menu_items = MenuItem.query.filter_by(org_id=user.org_id).order_by(MenuItem.category, MenuItem.name_ru).all()
    
    items = []
    for item in menu_items:
        items.append({
            'id': item.id,
            'name_kz': item.name_kz,
            'name_ru': item.name_ru,
            'name_en': item.name_en,
            'category': item.category,
            'base_price': item.base_price,
            'calories_100g': item.calories_100g,
            'image_url': item.image_url
        })
    
    return jsonify({'items': items})
