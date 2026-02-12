from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from app import create_app, db
from app.models import User
from seed import seed_data

app = create_app()

with app.app_context():
    db.create_all()

    # если пользователей нет — значит база пустая, сидим
    if User.query.count() == 0:
        seed_data()
        print("Seeded initial data (users/menu/etc).")
    else:
        print("DB already has users, skip seed.")
