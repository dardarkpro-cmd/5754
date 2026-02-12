import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    
    # Config - fix postgres:// to postgresql:// for SQLAlchemy 1.4+
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JWT — use a stable secret from env; fallback for local dev only
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        print("⚠ WARNING: JWT_SECRET_KEY not set! Using insecure fallback. Set it in production!")
        jwt_secret = 'dev-insecure-fallback-key'
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # CORS — allow Vercel frontend, localhost, and any FRONTEND_URL
    frontend_url = os.getenv('FRONTEND_URL', '')
    allowed_origins = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ]
    if frontend_url:
        # Support comma-separated list: "https://a.vercel.app,https://b.vercel.app"
        for origin in frontend_url.split(','):
            origin = origin.strip().rstrip('/')
            if origin and origin not in allowed_origins:
                allowed_origins.append(origin)

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}},
         supports_credentials=True)
    
    # Import models for migrations
    from app import models  # noqa
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok'}
    
    # Register blueprints
    from app.routes import auth, menu, orders, cook, pickup
    from app.routes import admin
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(menu.bp, url_prefix='/api')
    app.register_blueprint(orders.bp, url_prefix='/api')
    app.register_blueprint(cook.bp, url_prefix='/api/cook')
    app.register_blueprint(pickup.bp, url_prefix='/api')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    
    return app
from flask import jsonify

def create_app():
    app = Flask(__name__)
    # ... твоя конфигурация и register_blueprints ...

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True}), 200

    return app
