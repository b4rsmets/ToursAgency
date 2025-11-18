from flask import Flask
from models import db, User, Tour
from werkzeug.security import generate_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bars@localhost:5432/toursDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def init_database():
    with app.app_context():
        print("🗃️ Создание таблиц...")
        db.create_all()

        # Добавляем тестовые данные туров
        if Tour.query.count() == 0:
            tours = [
                Tour(
                    name='Парижский романтизм',
                    description='Романтическая прогулка по Парижу с посещением Эйфелевой башни и Лувра.',
                    price=1500.0,
                    duration_days=7,
                    destination='Париж, Франция',
                    image_url='https://images.unsplash.com/photo-1502602898536-47ad22581b52?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
                ),
                Tour(
                    name='Горные приключения в Альпах',
                    description='Трекинг и катание на лыжах в швейцарских Альпах.',
                    price=2500.0,
                    duration_days=10,
                    destination='Альпы, Швейцария',
                    image_url='https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
                ),
                Tour(
                    name='Пляжный релакс на Бали',
                    description='Расслабьтесь на белоснежных пляжах с йогой и спа.',
                    price=2000.0,
                    duration_days=14,
                    destination='Бали, Индонезия',
                    image_url='https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
                )
            ]
            db.session.bulk_save_objects(tours)
            print("✅ Тестовые туры добавлены!")
        else:
            print("ℹ️ Туры уже существуют")

        # Создаем пользователей с отключенным autoflush чтобы избежать ошибок
        with db.session.no_autoflush:
            # Администратор
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@tours.com',
                    role='admin'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                print("✅ Администратор создан")
            else:
                print("ℹ️ Администратор уже существует")

            # Тестовый пользователь
            if not User.query.filter_by(username='user').first():
                test_user = User(
                    username='user',
                    email='user@example.com',
                    role='user'
                )
                test_user.set_password('user123')
                db.session.add(test_user)
                print("✅ Тестовый пользователь создан")
            else:
                print("ℹ️ Тестовый пользователь уже существует")

        try:
            db.session.commit()
            print("\n🎉 База данных успешно инициализирована!")
            print("\n📋 Доступные учетные записи:")
            print("👑 Администратор - admin / admin123")
            print("👤 Пользователь - user / user123")
            print(f"\n📊 Статистика:")
            print(f"🏨 Туров: {Tour.query.count()}")
            print(f"👥 Пользователей: {User.query.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    init_database()