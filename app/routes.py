from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from pytdx.hq import TdxHq_API
import re
from flask_login import login_user, logout_user, login_required
from app import db
from app.models import User,  Admin, Stock, Trade, Sender, Reciver
from app.forms import LoginForm, OrderForm, QueryForm, TaskForm, TradeQueryForm
from datetime import datetime
from app.logging_config import logger
from app.tasks import send_msg, start_query
from config import Config

bp = Blueprint('main', __name__)

def get_price(code):
    match_res = re.compile(r'(\d{6}).([A-Z]{4})').search(code)
    if not match_res:
        logger.error(f"非法的股票代码格式: {code}")
        return None
    tmp_code = match_res.group(1)  # 股票代码
    mkt = 1 if match_res.group(2) == "XSHG" else 0  # # 市场类型（XSHG 或 XSHE）转换为1,0
    api = TdxHq_API()
    if api.connect(Config.TDX_HOST, 7709):
        stock_data = api.get_security_quotes(mkt,tmp_code)[0]
        data = {
            'code': stock_data['code'],
            'time': stock_data['reversed_bytes0'],
            'buy': [stock_data['bid1']/10,stock_data['bid2']/10,stock_data['bid3']/10] if tmp_code[0] in ['1','5'] else [stock_data['bid1'],stock_data['bid2'],stock_data['bid3']],
            'b_vol': [stock_data['bid_vol1'],stock_data['bid_vol2'],stock_data['bid_vol3']],
            'sell': [stock_data['ask1']/10,stock_data['ask2']/10,stock_data['ask3']/10] if tmp_code[0] in ['1','5'] else [stock_data['ask1'],stock_data['ask2'],stock_data['ask3']],
            's_vol': [stock_data['ask_vol1'],stock_data['ask_vol2'],stock_data['ask_vol3']],
        }
        api.disconnect()
        return data
    else:
        logger.error("无法连接到行情服务器")
        return None

def order(data, type):
    choice= {
        'SELL': ['buy', 'b_vol'],
        'BUY': ['sell', 's_vol']
    }
    rec = get_price(data.get('code', ''))
    pri = choice[type][0]
    vol = choice[type][1]
    if rec:
        if rec[pri][0] == 0.0:
            return "已经涨停无法买入" if pri == 'sell' else "已经跌停无法卖出", False
        pct = data.get('pct', 0)
        # amt = int(pct / rec[pri][1] / 100) * 100
        amt = pct
        if (amt / 100) < (rec[vol][0] + rec[vol][1]):
            price = rec[pri][1]
        else:
            price = rec[pri][2]
        now1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"{now1}时间：{rec['time']} {type}账号：{data.get('strategy','')} 金额：{price * amt} 价格：{price} 数量：{amt}")
        message_data = {
            'stg': data.get('strategy','537'),
            'type': type,
            'code': data.get('code', ''),
            'amt': amt,
            'price': price,
            'ttype' : ""
        }
        return message_data, True
    else:
        return "无法连接TDX服务器", False

@bp.route('/')
def index():
    return redirect(url_for('main.login'))

@bp.route('/api', methods=['POST'])
def api():
    try:
        data = request.json
        logger.info(f"收到数据：{data}")
        type = data.get('type', '')
        if type == 'BUY' or type == 'SELL':
            message_data, ret = order(data, type)
            if ret:
                send_msg(message_data)
                return jsonify({"answer": message_data}), 200
            else:
                return jsonify({"answer": message_data}), 500               
        elif type in ['BALANCE', 'POSITION', 'TRADE']:
            message_data = {
                'type': type,
                'stg': data.get('strategy','537')
            }
            send_msg(message_data)
            return jsonify({"answer": message_data}), 200
        else:
            logger.error(f"未知类型：{type} \n")
            return jsonify({"answer": "未知类型"}), 203
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"answer": f"{e}"}), 500


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
    if 'userid' not in session:
        session['userid'] = 536
        
    if request.method == 'POST':
        form = QueryForm(request.form)
        if form.validate():
            session['userid'] = int(form.userid.data)
        return redirect(url_for('main.account'))
    
    form = QueryForm()
    account = User.query.filter_by(id=session['userid']).first()
    stocks = Stock.query.filter_by(user_id=session['userid']).all()
    return render_template('account.html', account=account, stocks=stocks, form=form, link=url_for('main.account'))

@bp.route('/orders')
@login_required
def orders():
    orders = Stock.query.filter_by(user_id=session.get('userid', 536)).all()
    return render_template('orders.html', orders=orders)

@bp.route('/trades', methods=['GET', 'POST'])
@login_required
def trades():
    form = TradeQueryForm()
    
    # 初始化用户选择
    users = User.query.with_entities(User.id).distinct().all()
    form.user_id.choices = [(user.id, f'账户 {user.id}') for user in users]
    
    # 处理表单提交
    if form.validate_on_submit():
        start_date = form.start_date.data.strftime('%Y%m%d')
        end_date = form.end_date.data.strftime('%Y%m%d')
        user_id = form.user_id.data
        
        # 查询交易记录
        trades = Trade.query.filter(
            Trade.send_day.between(start_date, end_date),
            Trade.user_id == user_id
        ).order_by(Trade.send_day.desc(), Trade.start_time.desc()).all()
    else:
        # 默认显示当天数据
        today = datetime.now().strftime('%Y%m%d')
        trades = Trade.query.filter(
            Trade.send_day == today,
            Trade.user_id == session.get('userid', 536)
        ).order_by(Trade.start_time.desc()).all()
        form.start_date.data = datetime.now().date()
        form.end_date.data = datetime.now().date()
           
    return render_template('trades.html',
                         trades=trades,
                         form=form,
                         selected_user_id=form.user_id.data or session.get('userid', 536),
                         link=url_for('main.trades'))

@bp.route('/place_order', methods=['GET', 'POST'])
@login_required
def place_order():
    
    if request.method == 'POST':
        form_id = request.form.get('form_id')
        if form_id == 'form1':
            form = QueryForm(request.form)
            if form.validate():
                session['userid'] = int(form.userid.data)
        else:
            form = OrderForm(request.form)
            # 重新设置code_select的choices
            stocks = Stock.query.filter_by(user_id=session.get('userid', 536)).all()
            stock_choices = [(str(stock.stock_code), f"{stock.stock_code} - {stock.stock_name}") for stock in stocks]
            form.code_select.choices = stock_choices if stock_choices else [('', '暂无持仓')]
            
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
                send.user_id = session.get('userid', 536)
                tmp_code = f"{send.code}.{send.shorsz}"
                tmp_price = float(send.price)
                logger.info(f"{tmp_code} {tmp_price} {send.volume} {send.type} {session.get('userid', 536)}")
                try:
                    db.session.add(send)
                    db.session.commit()
                    
                    message_data = {
                        'stg': str(session.get('userid', 536)),
                        'type': send.type,
                        'code': tmp_code,
                        'amt': send.volume,
                        'price': tmp_price,
                        'ttype' : ""
                    }
                    
                    send_msg(message_data)
                       
                    flash('委托提交成功', 'success')
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"委托提交失败: {e}")
                    logger.exception(e)
                    flash('委托提交失败，请重试', 'danger')
                    return redirect(url_for('main.place_order'))
            else:
                logger.error(f"错误信息:{form.errors}")

        # 创建委托记录
        return redirect(url_for('main.place_order'))

    # 获取用户最近的委托记录和持仓数据
    form = QueryForm()
    form1 = OrderForm()
    account = User.query.filter_by(id=session.get('userid', 536)).first()
    stocks = Stock.query.filter_by(user_id=session.get('userid', 536)).all()  # 获取持仓数据
    recent_orders = Sender.query.filter_by(user_id=session.get('userid', 536)).order_by(Sender.meeting_day.desc(),Sender.start_time).limit(10).all()
    
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

    if request.method == 'POST':
        form = TaskForm(request.form)
        if form.validate():
            if form.type.data == 'CANCEL':
                # 取消所有委托
                send = Sender()
                now = datetime.now()
                send.meeting_day = now.strftime("%Y%m%d")
                send.start_time = now.strftime("%H:%M:%S")
                send.type = "CANCEL"
                send.user_id = int(form.userid.data)
                send.volume = 1
                send.code = "600000"
                send.shorsz = "XSHG"
                send.price = 1.00
                db.session.add(send)
                db.session.commit()
                message_data = {
                    'code': f"{send.code}.{send.shorsz}",
                    'amt': send.volume, 
                    'type': send.type, 
                    'ttype': "", 
                    'price': 1.00, 
                    'stg': str(send.user_id)      
                }
                
                send_msg(message_data)
            else:
                # 启动定时任务
                
                start_query(str(form.userid.data))                

        return redirect(url_for('main.tasks'))
    # 获取用户最近的委托记录和持仓数据
    form = TaskForm()
    recive = Reciver.query.filter(Reciver.meeting_day == datetime.now().strftime("%Y%m%d")).order_by(Reciver.start_time.desc()).limit(20).all()

    return render_template('tasks.html', form=form, orders=recive, link=url_for('main.tasks'))