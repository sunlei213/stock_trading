from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .redis_client import redis_client
from app import db
from app.models import User, Account, Order, Trade

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('main.account'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/account')
@login_required
def account():
    account = Account.query.filter_by(user_id=current_user.id).first()
    return render_template('account.html', account=account)

@bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)

@bp.route('/trades')
@login_required
def trades():
    trades = Trade.query.filter_by(user_id=current_user.id).all()
    return render_template('trades.html', trades=trades)

@bp.route('/place_order', methods=['GET', 'POST'])
@login_required
def place_order():
    if request.method == 'POST':
        stock_symbol = request.form['stock_symbol']
        stock_name = request.form['stock_name']
        order_type = request.form['order_type']
        order_price = float(request.form['order_price'])
        order_quantity = int(request.form['order_quantity'])
        order_amount = float(request.form['order_amount'])

        # 创建委托记录
        order = Order(
            user_id=current_user.id,
            stock_symbol=stock_symbol,
            stock_name=stock_name,
            order_type=order_type,
            order_price=order_price,
            order_quantity=order_quantity,
            order_amount=order_amount,
            status='待成交'
        )
        db.session.add(order)
        db.session.commit()

        flash('委托提交成功', 'success')
        return redirect(url_for('main.place_order'))

    # 获取用户最近的委托记录
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.order_time.desc()).limit(10).all()
    return render_template('place_order.html', recent_orders=recent_orders)