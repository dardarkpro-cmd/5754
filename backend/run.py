"""
Entry point for Smart Canteen backend.
- Gunicorn (Render): gunicorn run:app
- Local dev:          python run.py
On first launch auto-creates tables and seeds data if DB is empty.
"""
from app import create_app, db
from app.models import User
from sqlalchemy import text

app = create_app()

# Auto-create tables + migrate missing columns + seed
with app.app_context():
    db.create_all()

    # --- Migrate: add missing columns to existing tables ---
    # db.create_all() only creates NEW tables, it won't add columns
    # to tables that already exist. We handle that here.
    migrations = [
        ("orders", "pickup_code", "ALTER TABLE orders ADD COLUMN pickup_code VARCHAR(6)"),
        ("orders", "ready_at", "ALTER TABLE orders ADD COLUMN ready_at TIMESTAMP"),
        ("orders", "picked_up_at", "ALTER TABLE orders ADD COLUMN picked_up_at TIMESTAMP"),
    ]

    for table, column, sql in migrations:
        try:
            # Check if column exists
            result = db.session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :column"
            ), {"table": table, "column": column})
            if result.fetchone() is None:
                db.session.execute(text(sql))
                db.session.commit()
                print(f"✓ Added column {table}.{column}")
            else:
                print(f"  Column {table}.{column} already exists")
        except Exception as e:
            db.session.rollback()
            print(f"⚠ Migration {table}.{column}: {e}")

    # --- Seed if DB is empty ---
    if User.query.count() == 0:
        from seed import seed_data
        seed_data()
        print("✓ Seeded initial data (first launch).")
    else:
        print(f"DB has {User.query.count()} users, skip seed.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
