from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, redis_client
from app.models import User,  Admin, Stock, Trade, Sender
from app.forms import LoginForm, OrderForm, QueryForm
from datetime import datetime
from app.logging_config import logger

bp = Blueprint('main', __name__)

userid = 536

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.validate_password(password):
            login_user(admin)
            return redirect(url_for('main.account'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/account', methods=['GET'])
@login_required
def account():
    global userid
    userid = int(request.args.get('userid','536'))
    form = QueryForm()
    account = User.query.filter_by(id=userid).first()
    stocks = Stock.query.filter_by(user_id=userid).all()
    return render_template('account.html', account=account, stocks=stocks, form=form, link=url_for('main.account'))

@bp.route('/orders')
@login_required
def orders():
    global userid
    orders = Stock.query.filter_by(user_id=userid).all()
    return render_template('orders.html', orders=orders)

@bp.route('/trades')
@login_required
def trades():
    global userid
    trades = Trade.query.filter_by(user_id=userid).all()
    return render_template('trades.html', trades=trades)

@bp.route('/place_order', methods=['GET', 'POST'])
@login_required
def place_order():
    global userid
    if request.method == 'POST':
        form = OrderForm(request.form)
        if form.validate():
            send = Sender()
            form.populate_obj(send)
            now = datetime.now()
            send.meeting_day = now.strftime("%Y%m%d")
            send.start_time = now.strftime("%H:%M:%S")
            send.code = f"{send.code:0>6}"
            send.user_id = int(userid)
            tmp_code = f"{send.code}.{send.shorsz}"
            tmp_price = float(send.price)
            logger.info(f"{tmp_code} {tmp_price} {send.volume} {send.type} {userid}")
            db.session.add(send)
            db.session.commit()
            message_data = {
                'code': tmp_code,
                'amt': send.volume, 
                'type': send.type, 
                'price': tmp_price, 
                'stg': str(userid)      
            }
            redis_client.send_command("test", message_data)
            flash('委托提交成功', 'success')
        else:
            logger.error(f"错误信息:{form.errors}")

        # 创建委托记录
        return redirect(url_for('main.place_order'))

    # 获取用户最近的委托记录
    userid = int(request.args.get('userid','536'))
    form = QueryForm()
    form1 = OrderForm()
    account = User.query.filter_by(id=userid).first()
    recent_orders = Trade.query.filter_by(user_id=userid).order_by(Trade.start_time.desc()).limit(10).all()
    return render_template('place_order.html', recent_orders=recent_orders, account=account, form=form, form1=form1, link=url_for('main.place_order'))