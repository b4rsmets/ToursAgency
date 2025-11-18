# create_tables.py
from app import app, db
from models import User, Tour, Order


def create_tables():
    with app.app_context():
        try:
            # Создаем все таблицы
            db.create_all()
            print("✅ Все таблицы созданы успешно!")

            # Проверяем создание таблицы orders
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print("📊 Созданные таблицы:", tables)

        except Exception as e:
            print(f"❌ Ошибка при создании таблиц: {e}")


if __name__ == '__main__':
    create_tables()