"""
Menu routes - GET /menu
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import MenuItem, Inventory, Location, User

bp = Blueprint('menu', __name__)


@bp.route('/menu', methods=['GET'])
@jwt_required()
def get_menu():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'user_not_found'}), 404
    
    # Get user's location (first location in org for MVP)
    location = Location.query.filter_by(org_id=user.org_id).first()
    
    if not location:
        return jsonify({'error': 'location_not_found'}), 404
    
    if location.is_closed_manual:
        return jsonify({
            'error': 'location_closed',
            'message': 'Столовая сейчас закрыта'
        }), 403
    
    # Calculate weekday (1=Mon, 7=Sun) and menu_day (1-5, weekend->1)
    today = datetime.now()
    weekday = today.isoweekday()  # 1=Mon, 7=Sun
    
    # Check for day param override (1-5)
    day_param = request.args.get('day', type=int)
    if day_param and 1 <= day_param <= 5:
        menu_day = day_param
    else:
        # Weekend fallback to Monday menu
        menu_day = weekday if weekday <= 5 else 1
    
    # Get menu items with inventory (filtered by menu_day)
    items = []
    menu_items = MenuItem.query.filter_by(org_id=user.org_id, menu_day=menu_day).all()
    
    for item in menu_items:
        inv = Inventory.query.filter_by(
            location_id=location.id,
            menu_item_id=item.id
        ).first()
        
        items.append({
            'id': item.id,
            'name': item.name_ru,  # TODO: i18n based on user.language
            'name_kz': item.name_kz,
            'name_ru': item.name_ru,
            'category': item.category,
            'price': item.base_price,
            'is_available': inv.is_available if inv else False,
            'stock_qty': inv.stock_qty if inv else 0,
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
        'meal_slot': request.args.get('meal_slot', 'lunch'),
        'meta': {
            'today': weekday,      # 1=Mon..7=Sun (actual today)
            'showing': menu_day    # 1-5 (which day's menu is shown)
        },
        'items': items
    })

