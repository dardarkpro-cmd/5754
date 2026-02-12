"""
Entry point for Smart Canteen backend.
- Gunicorn (Render): gunicorn run:app
- Local dev:          python run.py
On first launch auto-creates tables and seeds data if DB is empty.
"""
from app import create_app, db
from app.models import User

app = create_app()

# Auto-create tables + seed on first launch
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        from seed import seed_data
        seed_data()
        print("✓ Seeded initial data (first launch).")
    else:
        print("DB already has data, skip seed.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from flask import jsonify

@app.get("/api/health")
def health():
    return jsonify({"ok": True}), 200
