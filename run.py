from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import redis
from redis.connection import ConnectionPool
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
import time
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户模型
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# 模拟用户数据库
users = {'user1': {'password': 'password1'}}

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# 初始化Redis连接池
redis_pool = ConnectionPool(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB, max_connections=Config.REDIS_POOL_SIZE)

def get_redis_connection():
    return redis.Redis(connection_pool=redis_pool)

# 初始化本地数据库
def init_db():
    with sqlite3.connect(Config.SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                balance REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                order_id TEXT,
                symbol TEXT,
                quantity INTEGER,
                price REAL,
                status TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                trade_id TEXT,
                symbol TEXT,
                quantity INTEGER,
                price REAL
            )
        ''')
        conn.commit()

# 查询账户资金、委托和成交信息
def query_account_info():
    # 模拟查询账户资金
    balance = 100000.0  # 这里应该是从外部API获取的实时数据

    # 模拟查询当日委托
    orders = [
        {'order_id': '12345', 'symbol': 'AAPL', 'quantity': 100, 'price': 150.0, 'status': 'filled'},
        {'order_id': '67890', 'symbol': 'GOOGL', 'quantity': 50, 'price': 2800.0, 'status': 'pending'}
    ]

    # 模拟查询当日成交
    trades = [
        {'trade_id': '11111', 'symbol': 'AAPL', 'quantity': 100, 'price': 150.0},
        {'trade_id': '22222', 'symbol': 'GOOGL', 'quantity': 50, 'price': 2800.0}
    ]

    # 保存到本地数据库
    with sqlite3.connect(Config.SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO account (balance) VALUES (?)', (balance,))
        for order in orders:
            cursor.execute('''
                INSERT INTO orders (order_id, symbol, quantity, price, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (order['order_id'], order['symbol'], order['quantity'], order['price'], order['status']))
        for trade in trades:
            cursor.execute('''
                INSERT INTO trades (trade_id, symbol, quantity, price)
                VALUES (?, ?, ?, ?)
            ''', (trade['trade_id'], trade['symbol'], trade['quantity'], trade['price']))
        conn.commit()

# 定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(func=query_account_info, trigger="interval", seconds=20)
scheduler.start()

@app.route('/')
@login_required
def index():
    with sqlite3.connect(Config.SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM account ORDER BY timestamp DESC LIMIT 1')
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM orders ORDER BY timestamp DESC')
        orders = cursor.fetchall()
        cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC')
        trades = cursor.fetchall()
    return render_template('index.html', account=account, orders=orders, trades=trades)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/order', methods=['POST'])
@login_required
def place_order():
    symbol = request.form['symbol']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    order_type = request.form['order_type']

    # 将委托指令发送到Redis
    redis_client = get_redis_connection()
    order_id = str(int(time.time()))  # 生成一个简单的订单ID
    order_data = {
        'order_id': order_id,
        'symbol': symbol,
        'quantity': quantity,
        'price': price,
        'order_type': order_type
    }
    redis_client.rpush('orders', str(order_data))

    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)