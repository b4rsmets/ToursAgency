import os
import ssl
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Tour, Order

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Выберите только одну конфигурацию базы данных:

# Вариант 1: Для локальной разработки
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bars@localhost:5432/toursDB'
database_url = 'postgresql+pg8000://tours:6ACpslgGZwopNuWfSGlsBFgjZV2Y4Fi0@dpg-d520bvshg0os73cm2s3g-a.oregon-postgres.render.com/tours_zt2q'
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl_context': ssl.create_default_context()
    }
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_today():
    return {'today': datetime.now().date()}


def init_database():
    """Инициализация базы данных при первом запуске"""
    with app.app_context():
        db.create_all()

        # Создаем администратора если его нет
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@tours.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Администратор создан (логин: admin, пароль: admin123)")

        # Создаем тестового пользователя если его нет
        if not User.query.filter_by(username='user').first():
            user = User(username='user', email='user@example.com', role='user')
            user.set_password('user123')
            db.session.add(user)
            print("✅ Тестовый пользователь создан (логин: user, пароль: user123)")

        # Добавляем тестовые туры если их нет
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
            print("✅ Тестовые туры добавлены")

        try:
            db.session.commit()
            print("✅ База данных инициализирована успешно!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка инициализации: {e}")


# Главная страница
@app.route('/')
def index():
    try:
        tours = Tour.query.all()
    except Exception as e:
        print(f"Ошибка при загрузке туров: {e}")
        tours = []
    return render_template('index.html', tours=tours)


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Это имя пользователя уже занято!', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Этот email уже используется!', 'error')
            return render_template('register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')

    return render_template('login.html')


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы.', 'info')
    return redirect(url_for('index'))


# Бронирование тура
@app.route('/book/<int:tour_id>', methods=['GET', 'POST'])
@login_required
def book_tour(tour_id):
    tour = Tour.query.get_or_404(tour_id)

    if request.method == 'POST':
        try:
            guests_count = int(request.form['guests_count'])
            start_date_str = request.form['start_date']
            contact_phone = request.form['contact_phone']
            contact_email = request.form['contact_email']
            special_requests = request.form.get('special_requests', '')

            # Валидация данных
            if guests_count < 1 or guests_count > 10:
                flash('Количество гостей должно быть от 1 до 10', 'error')
                return render_template('book_tour.html', tour=tour)

            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if start_date < datetime.now().date():
                flash('Дата начала не может быть в прошлом', 'error')
                return render_template('book_tour.html', tour=tour)

            end_date = start_date + timedelta(days=tour.duration_days)

            order = Order(
                user_id=current_user.id,
                tour_id=tour.id,
                guests_count=guests_count,
                total_price=tour.price * guests_count,
                start_date=start_date,
                end_date=end_date,
                contact_phone=contact_phone,
                contact_email=contact_email,
                special_requests=special_requests,
                status='Ожидание'
            )

            db.session.add(order)
            db.session.commit()

            flash('Тур успешно забронирован! Ожидайте подтверждения от администратора.', 'success')
            return redirect(url_for('my_orders'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при бронировании: {str(e)}', 'error')

    return render_template('book_tour.html', tour=tour)


# Мои заказы
@app.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)


# Управление заказами (для админов)
@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin():
        flash('У вас нет прав для доступа к этой странице!', 'error')
        return redirect(url_for('index'))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders)


# Изменение статуса заказа
@app.route('/order/<int:order_id>/update-status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin():
        flash('У вас нет прав для этой операции!', 'error')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)
    new_status = request.form['status']

    if new_status in ['Ожидание', 'Подтвержден', 'Отменен', 'Завершен']:
        order.status = new_status
        db.session.commit()

        # Сообщения для разных статусов
        status_messages = {
            'Ожидание': 'Заказ возвращен в ожидание',
            'Подтвержден': 'Заказ подтвержден! Уведомление отправлено клиенту.',
            'Отменен': 'Заказ отменен. Клиент будет уведомлен.',
            'Завершен': 'Заказ завершен. Спасибо за сотрудничество!'
        }

        flash(f'Статус заказа #{order.id} изменен на "{new_status}". {status_messages[new_status]}', 'success')
    else:
        flash('Неверный статус', 'error')

    return redirect(url_for('admin_orders'))


# Отмена заказа пользователем
@app.route('/order/<int:order_id>/cancel')
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id and not current_user.is_admin():
        flash('У вас нет прав для отмены этого заказа!', 'error')
        return redirect(url_for('index'))

    # Проверяем, можно ли отменить заказ
    if order.status == 'Завершен':
        flash('Нельзя отменить завершенный заказ', 'error')
        return redirect(url_for('my_orders'))

    if order.status == 'Отменен':
        flash('Этот заказ уже отменен', 'info')
        return redirect(url_for('my_orders'))

    order.status = 'Отменен'
    db.session.commit()

    if order.user_id == current_user.id:
        flash('Ваш заказ успешно отменен. Если у вас есть вопросы, свяжитесь с нами.', 'success')
    else:
        flash('Заказ пользователя отменен', 'success')

    if current_user.is_admin():
        return redirect(url_for('admin_orders'))
    return redirect(url_for('my_orders'))


# Добавление тура (только для админов)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_tour():
    if not current_user.is_admin():
        flash('У вас нет прав для доступа к этой странице!', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        duration_days = int(request.form['duration_days'])
        destination = request.form['destination']
        image_url = request.form.get('image_url', 'https://via.placeholder.com/300x200?text=Tour+Image')

        new_tour = Tour(
            name=name,
            description=description,
            price=price,
            duration_days=duration_days,
            destination=destination,
            image_url=image_url
        )
        db.session.add(new_tour)
        db.session.commit()
        flash('Тур успешно добавлен!', 'success')
        return redirect(url_for('index'))

    return render_template('add_tour.html')


# Страница тура
@app.route('/tour/<int:tour_id>')
def tour_detail(tour_id):
    tour = Tour.query.get_or_404(tour_id)
    return render_template('tour_detail.html', tour=tour)


# Редактирование тура (только для админов)
@app.route('/edit/<int:tour_id>', methods=['GET', 'POST'])
@login_required
def edit_tour(tour_id):
    if not current_user.is_admin():
        flash('У вас нет прав для доступа к этой странице!', 'error')
        return redirect(url_for('index'))

    tour = Tour.query.get_or_404(tour_id)

    if request.method == 'POST':
        tour.name = request.form['name']
        tour.description = request.form['description']
        tour.price = float(request.form['price'])
        tour.duration_days = int(request.form['duration_days'])
        tour.destination = request.form['destination']
        tour.image_url = request.form.get('image_url', tour.image_url)
        db.session.commit()
        flash('Тур успешно обновлён!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_tour.html', tour=tour)


# Удаление тура (только для админов)
@app.route('/delete/<int:tour_id>')
@login_required
def delete_tour(tour_id):
    if not current_user.is_admin():
        flash('У вас нет прав для доступа к этой странице!', 'error')
        return redirect(url_for('index'))

    tour = Tour.query.get_or_404(tour_id)
    db.session.delete(tour)
    db.session.commit()
    flash('Тур успешно удалён!', 'success')
    return redirect(url_for('index'))


# Удаление заказа (для админов)
@app.route('/order/<int:order_id>/delete')
@login_required
def delete_order(order_id):
    if not current_user.is_admin():
        flash('У вас нет прав для этой операции!', 'error')
        return redirect(url_for('index'))

    order = Order.query.get_or_404(order_id)

    try:
        db.session.delete(order)
        db.session.commit()
        flash(f'Заказ #{order.id} успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении заказа: {str(e)}', 'error')

    return redirect(url_for('admin_orders'))


# Профиль пользователя
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    # Инициализируем базу данных
    init_database()

    # Запускаем приложение
    app.run(debug=True)