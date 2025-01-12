from flask import Blueprint, render_template, redirect, url_for, request, flash, g
from flask_login import login_user, logout_user, login_required
from app import db, redis_client
from app.models import User,  Admin, Stock, Trade, Sender
from app.forms import LoginForm, OrderForm, QueryForm, TaskForm
from datetime import datetime
from app.logging_config import logger
from app.tasks import scheduler, start_scheduler, stop_scheduler

bp = Blueprint('main', __name__)

class GlobalState:
    def __init__(self):
        self.userid = 536
        self.is_task_running = False

g_state = GlobalState()

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        form = LoginForm(request.form)
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            admin = Admin.query.filter_by(username=username).first()
            if admin and admin.validate_password(password):
                login_user(admin)
                return redirect(url_for('main.account'))
            else:
                logger.error('用户名或密码无效')
                return redirect(url_for('main.login'))
    form = LoginForm()
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        form = QueryForm(request.form)
        if form.validate():
            g_state.userid = int(form.userid.data)
        return redirect(url_for('main.account'))
    
    form = QueryForm()
    account = User.query.filter_by(id=g_state.userid).first()
    stocks = Stock.query.filter_by(user_id=g_state.userid).all()
    return render_template('account.html', account=account, stocks=stocks, form=form, link=url_for('main.account'))

@bp.route('/orders')
@login_required
def orders():
    orders = Stock.query.filter_by(user_id=g_state.userid).all()
    return render_template('orders.html', orders=orders)

@bp.route('/trades')
@login_required
def trades():
    trades = Trade.query.filter_by(user_id=g_state.userid).all()
    return render_template('trades.html', trades=trades)

@bp.route('/place_order', methods=['GET', 'POST'])
@login_required
def place_order():
    if request.method == 'POST':
        form_id = request.form.get('form_id')
        logger.info(f"form_id: {form_id}")
        if form_id == 'form1':
            form = QueryForm(request.form)
            if form.validate():
                g_state.userid = int(form.userid.data)
        else:
            form = OrderForm(request.form)
            if form.validate():
                send = Sender()
                form.populate_obj(send)
                if form.type.data == 'SELL':
                    send.code = form.code_select.data
                else:
                    send.code = form.code.data
                now = datetime.now()
                send.meeting_day = now.strftime("%Y%m%d")
                send.start_time = now.strftime("%H:%M:%S")
                send.code = f"{send.code:0>6}"
                send.user_id = int(g_state.userid)
                tmp_code = f"{send.code}.{send.shorsz}"
                tmp_price = float(send.price)
                logger.info(f"{tmp_code} {tmp_price} {send.volume} {send.type} {g_state.userid}")
                db.session.add(send)
                db.session.commit()
                message_data = {
                    'code': tmp_code,
                    'amt': send.volume, 
                    'type': send.type, 
                    'price': tmp_price, 
                    'stg': str(g_state.userid)      
                }
                redis_client.send_command("test", message_data)
                flash('委托提交成功', 'success')
            else:
                logger.error(f"错误信息:{form.errors}")

        # 创建委托记录
        return redirect(url_for('main.place_order'))

    # 获取用户最近的委托记录和持仓数据
    form = QueryForm()
    form1 = OrderForm()
    account = User.query.filter_by(id=g_state.userid).first()
    stocks = Stock.query.filter_by(user_id=g_state.userid).all()  # 获取持仓数据
    recent_orders = Sender.query.filter_by(user_id=g_state.userid).order_by(Sender.start_time.desc()).limit(10).all()
    
    # 构建股票代码选项
    stock_choices = [(str(stock.stock_code), f"{stock.stock_code} - {stock.stock_name}") for stock in stocks]
    form1.code_select.choices = stock_choices if stock_choices else [('', '暂无持仓')]
    
    # 将 stocks 转换为字典列表
    stocks_data = [{'stock_code': stock.stock_code, 'usedstock': stock.usedstock} for stock in stocks]
    
    return render_template('place_order.html', 
                         recent_orders=recent_orders, 
                         account=account, 
                         stocks=stocks_data,  # 传入可序列化的持仓数据
                         form=form, 
                         form1=form1, 
                         link=url_for('main.place_order'))

@bp.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = TaskForm()
    is_running = scheduler.running

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start' and not is_running:
            start_scheduler()
            logger.info("定时任务已启动")
            flash('定时任务已启动', 'success')
        elif action == 'stop' and is_running:
            stop_scheduler()
            logger.info("定时任务已停止")
            flash('定时任务已停止', 'success')
        return redirect(url_for('main.tasks'))

    return render_template('tasks.html', form=form, is_running=is_running)