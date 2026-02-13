"""
Seed data for Smart Canteen MVP
1 org, 1 location, 5 users, 10 menu items, 10 locker cells, 1 daily menu, 1 sample order
3 groups: 10A (school), CS-101 (university), Floor 3 (business)

Two entry points:
  - seed_data()  — called from run.py on first launch (no app context needed, caller provides it)
  - seed()       — standalone: python seed.py (creates its own app context)
"""
from datetime import time, date, datetime, timedelta
from werkzeug.security import generate_password_hash
from app import db, create_app
from app.models import (
    Organization, Location, User, MenuItem, Inventory, LockerCell,
    DailyMenu, DailyMenuItem, Order, OrderItem, Receipt,
    LockerReservation, PickupToken, Group
)


def seed_data():
    """Insert seed rows. Assumes caller has already set up app context and called db.create_all()."""

    # Clear existing data (order matters for FK constraints)
    PickupToken.query.delete()
    LockerReservation.query.delete()
    Receipt.query.delete()
    OrderItem.query.delete()
    Order.query.delete()
    DailyMenuItem.query.delete()
    DailyMenu.query.delete()
    LockerCell.query.delete()
    Inventory.query.delete()
    MenuItem.query.delete()
    # Clear group_id from users before deleting groups
    User.query.update({User.group_id: None})
    db.session.commit()
    User.query.delete()
    Group.query.delete()
    Location.query.delete()
    Organization.query.delete()
    db.session.commit()

    # Organization
    org = Organization(id='org-1', name='Школа №42')
    db.session.add(org)

    # Location
    loc = Location(
        id='loc-1',
        org_id='org-1',
        name='Столовая №1',
        opening_time=time(8, 0),
        closing_time=time(18, 0),
        is_closed_manual=False
    )
    db.session.add(loc)

    # Groups
    groups = [
        Group(id='group-1', org_id='org-1', name='10A', type='school'),
        Group(id='group-2', org_id='org-1', name='CS-101', type='university'),
        Group(id='group-3', org_id='org-1', name='Floor 3', type='business'),
    ]
    db.session.add_all(groups)
    db.session.flush()

    # Users (PIN = 123456)
    pin_hash = generate_password_hash('123456')
    users = [
        User(id='admin-1', org_id='org-1', role='admin', login='admin',
             pin_hash=pin_hash, display_name='Администратор'),
        User(id='cook-1', org_id='org-1', role='cook', login='cook',
             pin_hash=pin_hash, display_name='Повар Айгуль'),
        User(id='user-1', org_id='org-1', role='user', login='student1',
             pin_hash=pin_hash, display_name='Айбек К.', group_id='group-1'),
        User(id='user-2', org_id='org-1', role='user', login='student2',
             pin_hash=pin_hash, display_name='Дана М.'),
        User(id='user-3', org_id='org-1', role='user', login='student3',
             pin_hash=pin_hash, display_name='Арман Т.'),
    ]
    db.session.add_all(users)

    # Menu Items
    items = [
        MenuItem(id='item-1', org_id='org-1', name_kz='Борщ', name_ru='Борщ',
                 category='first', base_price=450, calories_100g=45, menu_day=1),
        MenuItem(id='item-2', org_id='org-1', name_kz='Шурпа', name_ru='Шурпа',
                 category='first', base_price=500, calories_100g=55, menu_day=1),
        MenuItem(id='item-3', org_id='org-1', name_kz='Плов', name_ru='Плов',
                 category='second', base_price=650, calories_100g=180, menu_day=2),
        MenuItem(id='item-4', org_id='org-1', name_kz='Котлета', name_ru='Котлета',
                 category='second', base_price=400, calories_100g=220, menu_day=2),
        MenuItem(id='item-5', org_id='org-1', name_kz='Рис', name_ru='Рис',
                 category='second', base_price=200, calories_100g=130, menu_day=3),
        MenuItem(id='item-6', org_id='org-1', name_kz='Салат', name_ru='Салат',
                 category='salads', base_price=300, calories_100g=35, menu_day=3),
        MenuItem(id='item-7', org_id='org-1', name_kz='Компот', name_ru='Компот',
                 category='drinks', base_price=150, calories_100g=40, menu_day=4),
        MenuItem(id='item-8', org_id='org-1', name_kz='Чай', name_ru='Чай',
                 category='drinks', base_price=100, calories_100g=0, menu_day=4),
        MenuItem(id='item-9', org_id='org-1', name_kz='Пирожок', name_ru='Пирожок',
                 category='desserts', base_price=200, calories_100g=290, menu_day=5),
        MenuItem(id='item-10', org_id='org-1', name_kz='Булочка', name_ru='Булочка',
                 category='desserts', base_price=180, calories_100g=310, menu_day=5),
    ]
    db.session.add_all(items)

    # Inventory
    inventory = [
        Inventory(id='inv-1', location_id='loc-1', menu_item_id='item-1',
                  is_available=True, stock_qty=50),
        Inventory(id='inv-2', location_id='loc-1', menu_item_id='item-2',
                  is_available=True, stock_qty=30),
        Inventory(id='inv-3', location_id='loc-1', menu_item_id='item-3',
                  is_available=True, stock_qty=40),
        Inventory(id='inv-4', location_id='loc-1', menu_item_id='item-4',
                  is_available=True, stock_qty=60),
        Inventory(id='inv-5', location_id='loc-1', menu_item_id='item-5',
                  is_available=True, stock_qty=100),
        Inventory(id='inv-6', location_id='loc-1', menu_item_id='item-6',
                  is_available=True, stock_qty=25),
        Inventory(id='inv-7', location_id='loc-1', menu_item_id='item-7',
                  is_available=True, stock_qty=80),
        Inventory(id='inv-8', location_id='loc-1', menu_item_id='item-8',
                  is_available=True, stock_qty=None),
        Inventory(id='inv-9', location_id='loc-1', menu_item_id='item-9',
                  is_available=True, stock_qty=20),
        Inventory(id='inv-10', location_id='loc-1', menu_item_id='item-10',
                  is_available=False, stock_qty=0),
    ]
    db.session.add_all(inventory)

    # Locker Cells A1-A10
    cells = [
        LockerCell(id=f'cell-{i}', location_id='loc-1', code=f'A{i}', status='FREE')
        for i in range(1, 11)
    ]
    db.session.add_all(cells)

    # Daily Menu for today
    today = date.today()
    dm = DailyMenu(
        id='dm-1',
        location_id='loc-1',
        menu_date=today,
        meal_slot='lunch',
        created_by='cook-1'
    )
    db.session.add(dm)
    db.session.flush()

    daily_items = [
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-1', stock_qty=50, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-2', stock_qty=30, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-3', stock_qty=40, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-4', stock_qty=60, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-5', stock_qty=100, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-6', stock_qty=25, is_available=True),
        DailyMenuItem(daily_menu_id='dm-1', menu_item_id='item-7', stock_qty=80, is_available=True),
    ]
    db.session.add_all(daily_items)

    # Sample order (PAID)
    sample_order = Order(
        id='order-demo-1',
        user_id='user-1',
        location_id='loc-1',
        status='PAID',
        scheduled_for=datetime.utcnow() + timedelta(minutes=30),
        total=1100
    )
    db.session.add(sample_order)
    db.session.flush()

    demo_items = [
        OrderItem(order_id='order-demo-1', menu_item_id='item-1', qty=1, unit_price=450),
        OrderItem(order_id='order-demo-1', menu_item_id='item-3', qty=1, unit_price=650),
    ]
    db.session.add_all(demo_items)

    db.session.commit()
    print("✓ Seed data created successfully!")
    print("  - 1 organization, 1 location, 5 users, 10 menu items")
    print("  - 3 groups (10A, CS-101, Floor 3), student1 → 10A")
    print("  - 10 locker cells, 1 daily menu, 1 sample PAID order")


def seed():
    """Standalone entry point: creates app context, then seeds."""
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_data()


if __name__ == '__main__':
    seed()
