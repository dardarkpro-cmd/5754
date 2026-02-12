"""
Smart Canteen - Database Models
All 11 tables for Sprint 1
"""
import uuid
from datetime import datetime, date as date_type
from app import db


def generate_uuid():
    return str(uuid.uuid4())


# ==================== Core Tables ====================

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    locations = db.relationship('Location', backref='organization', lazy='dynamic')
    users = db.relationship('User', backref='organization', lazy='dynamic')
    menu_items = db.relationship('MenuItem', backref='organization', lazy='dynamic')


class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    opening_time = db.Column(db.Time, nullable=False)
    closing_time = db.Column(db.Time, nullable=False)
    is_closed_manual = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    inventory = db.relationship('Inventory', backref='location', lazy='dynamic')
    orders = db.relationship('Order', backref='location', lazy='dynamic')
    locker_cells = db.relationship('LockerCell', backref='location', lazy='dynamic')


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user, cook, admin
    login = db.Column(db.String(100), nullable=False, unique=True)
    pin_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    language = db.Column(db.String(5), default='ru')
    theme = db.Column(db.String(10), default='light')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy='dynamic')


# ==================== Menu Tables ====================

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    org_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    name_kz = db.Column(db.String(255), nullable=False)
    name_ru = db.Column(db.String(255), nullable=False)
    name_en = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)  # first, second, salads, drinks, desserts
    base_price = db.Column(db.Integer, nullable=False)  # в тиынах
    calories_100g = db.Column(db.Integer)
    protein_100g = db.Column(db.Float)
    fat_100g = db.Column(db.Float)
    carbs_100g = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    menu_day = db.Column(db.Integer, default=1)  # 1=Mon..5=Fri
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    inventory = db.relationship('Inventory', backref='menu_item', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='menu_item', lazy='dynamic')


class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id'), nullable=False)
    menu_item_id = db.Column(db.String(36), db.ForeignKey('menu_items.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    stock_qty = db.Column(db.Integer)  # null = unlimited
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('location_id', 'menu_item_id', name='uq_inventory_location_item'),
    )


# ==================== Order Tables ====================

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='CREATED')
    scheduled_for = db.Column(db.DateTime, nullable=False)
    total = db.Column(db.Integer, nullable=False)  # в тиынах
    priority = db.Column(db.Integer, default=0)
    pickup_code = db.Column(db.String(6), nullable=True)  # 6-digit pickup code
    ready_at = db.Column(db.DateTime, nullable=True)
    picked_up_at = db.Column(db.DateTime, nullable=True)
    pickup_deadline_at = db.Column(db.DateTime)  # cell hold until
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('OrderItem', backref='order', lazy='dynamic')
    receipt = db.relationship('Receipt', backref='order', uselist=False)
    reservation = db.relationship('LockerReservation', backref='order', uselist=False)
    tokens = db.relationship('PickupToken', backref='order', lazy='dynamic')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.String(36), db.ForeignKey('menu_items.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Integer, nullable=False)
    modifiers_json = db.Column(db.JSON)
    comment = db.Column(db.String(500))


class Receipt(db.Model):
    __tablename__ = 'receipts'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, unique=True)
    receipt_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== Locker/Pickup Tables ====================

class LockerCell(db.Model):
    __tablename__ = 'locker_cells'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id'), nullable=False)
    code = db.Column(db.String(5), nullable=False)  # A1..A10
    status = db.Column(db.String(20), default='FREE')  # FREE, RESERVED, OCCUPIED
    
    __table_args__ = (
        db.UniqueConstraint('location_id', 'code', name='uq_cell_location_code'),
    )
    
    reservations = db.relationship('LockerReservation', backref='cell', lazy='dynamic')


class LockerReservation(db.Model):
    __tablename__ = 'locker_reservations'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False, unique=True)
    cell_id = db.Column(db.String(36), db.ForeignKey('locker_cells.id'), nullable=False)
    hold_until = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    released_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.Index('idx_active_cell_reservation', 'cell_id', 
                 postgresql_where=(db.text('released_at IS NULL'))),
    )


class PickupToken(db.Model):
    __tablename__ = 'pickup_tokens'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    qr_token = db.Column(db.String(64), nullable=False, unique=True)
    pin_code = db.Column(db.String(6), nullable=False)
    token_expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_pickup_token_expires', 'token_expires_at',
                 postgresql_where=(db.text('used_at IS NULL'))),
    )


# ==================== Daily Menu Tables ====================

class DailyMenu(db.Model):
    __tablename__ = 'daily_menus'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    location_id = db.Column(db.String(36), db.ForeignKey('locations.id'), nullable=False)
    menu_date = db.Column(db.Date, nullable=False)
    meal_slot = db.Column(db.String(20), nullable=False, default='lunch')
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('location_id', 'menu_date', 'meal_slot', name='uq_daily_menu_loc_date_slot'),
    )
    
    items = db.relationship('DailyMenuItem', backref='daily_menu', lazy='dynamic',
                            cascade='all, delete-orphan')
    location = db.relationship('Location', backref='daily_menus')
    creator = db.relationship('User', backref='created_daily_menus')


class DailyMenuItem(db.Model):
    __tablename__ = 'daily_menu_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    daily_menu_id = db.Column(db.String(36), db.ForeignKey('daily_menus.id'), nullable=False)
    menu_item_id = db.Column(db.String(36), db.ForeignKey('menu_items.id'), nullable=False)
    stock_qty = db.Column(db.Integer, nullable=True)  # null = unlimited
    is_available = db.Column(db.Boolean, default=True)
    
    menu_item = db.relationship('MenuItem', backref='daily_menu_entries')

