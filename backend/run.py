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

    # --- Migrate: add missing columns / tables to existing DB ---
    migrations = [
        # Orders — pickup columns
        ("orders", "pickup_code", "ALTER TABLE orders ADD COLUMN pickup_code VARCHAR(6)"),
        ("orders", "ready_at", "ALTER TABLE orders ADD COLUMN ready_at TIMESTAMP"),
        ("orders", "picked_up_at", "ALTER TABLE orders ADD COLUMN picked_up_at TIMESTAMP"),
        # Users — group_id
        ("users", "group_id", "ALTER TABLE users ADD COLUMN group_id VARCHAR(36) REFERENCES groups(id)"),
    ]

    # Ensure groups table exists (db.create_all handles new tables)
    # But for safety, explicitly check:
    try:
        result = db.session.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'groups' AND table_schema = 'public'"
        ))
        if result.fetchone() is None:
            db.session.execute(text("""
                CREATE TABLE groups (
                    id VARCHAR(36) PRIMARY KEY,
                    org_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    CONSTRAINT uq_group_org_name UNIQUE (org_id, name)
                )
            """))
            db.session.commit()
            print("✓ Created table: groups")
        else:
            print("  Table groups already exists")
    except Exception as e:
        db.session.rollback()
        print(f"⚠ groups table migration: {e}")

    for table, column, sql in migrations:
        try:
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
