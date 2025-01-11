# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 10:25:20 2017

@author: sunlei
"""

from flask import Flask,request,redirect,url_for,render_template,flash
 
# For this example we'll use SQLAlchemy, a popular ORM that supports a
# variety of backends including SQLite, MySQL, and PostgreSQL
import json,os,sys
import time
import redis
from threading import Thread
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from wtforms.fields import StringField, SubmitField, SelectField, RadioField, DecimalField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length
from config import Config, redisConfig
import logging
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Query user by id in the cookie"""
    user = db.session.get(Admin, user_id)    #get(user_id)
    return user

login_manager.init_app(app)
login_manager.login_view = 'login'  # 指定未登录时重定向的视图函数
login_manager.login_message = '请先登录!'
login_manager.login_message_category = 'warning'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

is_start = True

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=redisConfig.host,
    port=redisConfig.port,
    password=redisConfig.pwd,
    db=0,
    decode_responses=True,
    max_connections=20,
    socket_timeout=8,           # 套接字操作超时 8 秒
    socket_connect_timeout=5,   # 连接建立超时 5 秒
    retry_on_timeout=True,      # 超时后重试
    health_check_interval=30    # 每 30 秒检查健康一次
)

def get_redis_connection():
    return redis.Redis(connection_pool=redis_pool)


def connect_redis():
    while True:
        try:
            # 创建Redis连接
            r = get_redis_connection()
            r.ping()
            return r
        except Exception as e:
            logging.error("redis连接失败,正在尝试重连")
            redis_pool.disconnect()
            time.sleep(2)


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError(f'password是只读属性')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Sender(db.Model):
    """A single meeting"""
    id = db.Column(db.Integer, primary_key=True)
    meeting_day = db.Column(db.String(8))
    start_time = db.Column(db.String(8))
    code = db.Column(db.String(6))
    shorsz = db.Column(db.String(4))
    price = db.Column(db.DECIMAL(10,3))
    volume = db.Column(db.Integer)
    type = db.Column(db.String(8))
    stg = db.Column(db.String(6))

class Reciver(db.Model):
    """A single meeting"""
    id = db.Column(db.Integer, primary_key=True)
    meeting_day = db.Column(db.String(8))
    start_time = db.Column(db.String(8))
    stg = db.Column(db.String(6))
    type = db.Column(db.String(8))
    msg = db.Column(db.String(100))

class Msg(object):
    #queue = []
    def __init__(self):
        self.thread1 = Thread(target=self.loop_test, daemon=True)
        self.thread2 = Thread(target=self.loop_consuming, daemon=True)
        self.stream_name = "msg"
        self.consumer_group = "msg_group"
        self.is_run = True


    def xgroup_create(self):
        """
        创建消费组
        """
        flag = self.check_consumer_group_exists()
        if flag:
            logging.info('消费者组已存在')            
        else:
            my_rds = get_redis_connection()
            my_rds.xgroup_create(self.stream_name, self.consumer_group, id='0', mkstream=True)
            logging.info('消费者组创建成功')

    def check_consumer_group_exists(self):
        # 获取指定Stream的消费者组列表
        try:
            my_rds = get_redis_connection()
            groups = my_rds.xinfo_groups(self.stream_name)
            return any(group['name'] == self.consumer_group for group in groups)
        except Exception as e:
            logging.error(f"检查消费者组时出错: {e}")
            return False

    def __get_data(self, data):
        """
        从消息流中获取业务数据
        """
        if not data or not data[0]:
            return None, None
        msgId = data[0]
        data = {key: val for key, val in data[1].items()}
        if not data.get("bizData"):
            return msgId, data
        return msgId, data["bizData"]
    
    def _process_message(self, data):
        if not data or 'type' not in data or 'ret' not in data:
            return None

        message_type = data.get('type', '')
        ret = data['ret']
        if message_type == 'CANCEL':
            logger.info(f'取消委托， 委托号：{type(data.get("msg"))}, 委托状态：{data.get("message", "N/A")}')
        try:
            msg = eval(data['msg']) if 'msg' in data else {}
        except:
            msg = data['msg'] if 'msg' in data else {}
        

        if ret == '1':
            if message_type == 'BALANCE':
                return f"金额：{msg.get('可用金额', 'N/A')}, 市值:{msg.get('股票市值', 'N/A')}, 总资产：{msg.get('总资产', 'N/A')}"
            if message_type in ('BUY', 'SELL'):
                return f"委托号：{msg.get('entrust_no', '0')},委托状态：{msg.get('message', '正常')}"
            if message_type == 'CANCEL':
                return msg
        return f"委托失败信息：{msg}"

    def _save_to_db(self, data, message):
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        now_time = now.strftime("%H:%M:%S")

        with app.app_context():
            reci = Reciver(
                meeting_day = today,
                start_time = now_time,
                stg = data['stg'],
                type = data['type'],
                msg = message
            )
            db.session.add(reci)
            db.session.commit()

    def consume(self, consumer_name: str, id: str = ">", block: int = 5000, count: int = 1)->bool:
        """
        从 Redis 流中消费消息，处理并保存结果到数据库。

        参数:
            consumer_name (str): 消费者名称（例如 IP 地址）。
            id (str): 消费的起始点，默认为 ">"，表示从流的末尾开始。
            block (int): 阻塞超时时间，单位为毫秒，默认为 5000（5 秒）。
            count (int): 一次消费的消息数量，默认为 1。

        返回:
            bool: 如果消费成功，返回 True；否则返回 False。
        """
        # block 0 时阻塞等待, 其他数值表示读取超时时间
        streams = {self.stream_name: id}
        try:
            my_rds = get_redis_connection()
            rst = my_rds.xreadgroup( self.consumer_group, consumer_name, streams, block=block, count=count)
            if not rst or not rst[0] or not rst[0][1]:
                return False
            # 处理每条消息
            for item in rst[0][1]:
                try:
                    #解析数据
                    msgId, data = self.__get_data(item)
                    if not data:
                        continue
                    """
                    执行回调函数target，成功后ack
                    """
                    logging.info(f'消费到的数据 {data}')
                    message = self._process_message(data)
                    if message:
                        self._save_to_db(data, message)
                        my_rds.xack(self.stream_name, self.consumer_group, msgId)
                        my_rds.xdel(self.stream_name, msgId)
                except Exception as e:
                    # 消费失败，下次从头消费(消费成功的都已经提交ack了，可以先不处理，以后再处理)
                    logging.error(f"consumer is error:{repr(e)}")
            return True
        except redis.RedisError as e:
            
            logging.error(f"网络连接超时，尝试重新连接{e}")
            return False

    def file2dict(self,path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
        
    def loop_consuming(self):
        #is_pop = True
        #log_time = datetime.now().strftime("%Y%m%d %H:%M:%S")
        logging.info("回报进程开始")
        while self.is_run:
            self.consume("consumer", count=3)

        logging.info("回报进程结束")
    
    def _check_redis_connection(self)->bool:
        """
        检查 Redis 连接是否活跃。

        通过尝试获取键为 "test" 的值来验证连接。如果成功，返回 True；如果发生异常，
        记录错误日志，并尝试重新连接 Redis，然后返回 False。

        参数:
            redis_connection (Redis): Redis 连接对象。

        返回:
            bool: 如果连接活跃且操作成功，返回 True；否则返回 False。
        """
        try:
            my_rds = get_redis_connection()
            my_rds.get("test")
            return True
        except Exception as e:
            now = datetime.now()
            #log_time = now.strftime("%Y%m%d %H:%M:%S")
            logging.error(f"{e} Redis连接失败，正在尝试重连")
            my_rds = connect_redis()
            return False

    def loop_test(self):
        global is_start
        logging.info("检测进程开始")
        while is_start:
            """
            while self.thread2.is_alive() and is_start:
                if not self._check_redis_connection():
                    self.is_run = False
                    time.sleep(30)
                    now = datetime.now()
                    log_time = now.strftime("%Y%m%d %H:%M:%S")
                    logging.info(f"{log_time} 重连成功，回报进程退出")
                    #break
                time.sleep(10)
            if not is_start:
                self.is_run = False
                break
            self.is_run = True
            self.thread2 = Thread(target=self.loop_consuming, daemon=True)
            self.thread2.start()
            logging.info("回报进程重新启动")"""
            self._check_redis_connection()
            time.sleep(30)
        logging.info("检测进程结束")

    def start_background(self):
        self.thread2.start()
        time.sleep(5)
        self.thread1.start()

class shutdownForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField('关闭服务器')

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField('登录')

class MeetForm(FlaskForm):
    code = IntegerField(u'代码：', validators=[DataRequired()])
    price = DecimalField(u'价格：', validators=[DataRequired()])
    volume = IntegerField(u'数量：', validators=[DataRequired()])
    stg = RadioField(
        '账户：',
        validators=[DataRequired()],
        choices=[
            ('537', '主账户'),
            ('536', '备账户')
        ]
    )
    shorsz = RadioField(
        '市场：',
        validators=[DataRequired()],
        choices=[
            ('XSHG', '沪'),
            ('XSHE', '深')
        ]
    )
    type = SelectField(
        '委托方式：',
        validators=[DataRequired()],
        choices=[
            ('BUY', '买入'),
            ('SELL', '卖出')
        ]
    )
    # submit button will read "share my lunch!"
    submit = SubmitField(u'提交会议')

class QueryForm(FlaskForm):
    stg = RadioField(
        '账户：',
        validators=[DataRequired()],
        choices=[
            ('537', '主账户'),
            ('536', '备账户')
        ]
    )
    type = SelectField(
        '委托方式：',
        validators=[DataRequired()],
        choices=[
            ('BALANCE', '查询'),
            ('CANCEL', '撤销')
        ]
    )
    # submit button will read "share my lunch!"
    submit = SubmitField(u'提交查询')

@app.route('/')
def index():
    return render_template('sample.htm', list1=[
        ('当天发送列表', url_for('v_list')),
        ('添加会议', url_for('add_m')),
        ('添加查询', url_for('query')),
        ('当天接受列表', url_for('query_m'))
    ])

@app.route('/login',methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('query_m'))
    list1=[
            ('当天发送列表', url_for('v_list')),
            ('添加会议', url_for('add_m')),
            ('添加查询', url_for('query')),
            ('当天接受列表', url_for('query_m'))
        ]
    if request.method == 'GET':
        form = LoginForm()
        return render_template('sample_quit.htm',list1=list1,form=form,link=url_for('login'))
    else:
        form = LoginForm(request.form)
        if form.validate():
            username = form.username.data
            password = form.password.data
            admin = Admin.query.first()          
            if admin:
                if username == admin.username and admin.validate_password(password):
                    login_user(admin)
                    flash('Login Success!', 'info')
                    return redirect(url_for('query_m'))
                flash('Invalid username or password!', 'warning')
            else:
                flash('No admin Account', 'warning')
        return render_template('sample_quit.htm',list1=list1,form=form,link=url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Success!', 'info')
    return redirect(url_for('login'))

@app.route('/quit')
@login_required
def quit():
    global is_start
    is_start = False
    flash('Server shutdown!', 'success')
    return redirect(url_for('index'))


@app.route('/ml')
@login_required
def v_list():
    now = datetime.now()
    today = '{0}{1:0>2}{2:0>2}'.format(now.year, now.month, now.day)
    meet_list = Sender.query.filter(Sender.meeting_day==today).order_by(Sender.start_time).all()
    title = '{0}年{1:0>2}月{2:0>2}日列表'.format(now.year, now.month, now.day)
    return render_template('sample_list.htm',list1=[
        ('当天发送列表', url_for('v_list')),
        ('添加会议', url_for('add_m')),
        ('添加查询', url_for('query')),
        ('当天接受列表', url_for('query_m'))
    ], list2=meet_list,title=title,back=url_for('index'))

@app.route('/qm')
@login_required
def query_m():
    now = datetime.now()
    today = '{0}{1:0>2}{2:0>2}'.format(now.year, now.month, now.day)
    meet_list = Reciver.query.filter(Reciver.meeting_day==today).order_by(Reciver.start_time).all()
    title = '{0}年{1:0>2}月{2:0>2}日列表'.format(now.year, now.month, now.day)
    return render_template('sample_rec.htm',list1=[
        ('当天发送列表', url_for('v_list')),
        ('添加会议', url_for('add_m')),
        ('添加查询', url_for('query')),
        ('当天接受列表', url_for('query_m'))
    ], list2=meet_list,title=title,back=url_for('index'))

@app.route('/add',methods=["GET","POST"])
@login_required
def add_m():
    if request.method == 'GET':
        form = MeetForm()
        #return render_template('sample_add.htm',list1=list1,form=form,link=url_for('add_m'))
    else:
        form = MeetForm(request.form)
        if form.validate():
            send = Sender()
            form.populate_obj(send)
            now = datetime.now()
            send.meeting_day = now.strftime("%Y%m%d")
            send.start_time = now.strftime("%H:%M:%S")
            send.code = f"{send.code:0>6}"
            tmp_code = f"{send.code}.{send.shorsz}"
            tmp_price = float(send.price)
            logging.info(f"{tmp_code} {tmp_price} {send.volume} {send.type} {send.stg}")
            db.session.add(send)
            db.session.commit()
            message_data = {
                'code': tmp_code,
                'amt': send.volume, 
                'type': send.type, 
                'price': tmp_price, 
                'stg': send.stg      
            }
            try:
                rds = get_redis_connection()
                rds.xadd("order", message_data)
            except Exception as e:
                logging.error(f'redis连接失败,正在尝试重连{e}')
            return redirect(url_for('add_m'))
        else:
            logging.error(f"错误信息:{form.errors}")
    return render_template('sample_add.htm',list1=[
        ('当天发送列表', url_for('v_list')),
        ('添加会议', url_for('add_m')),
        ('添加查询', url_for('query')),
        ('当天接受列表', url_for('query_m'))
    ],form=form,link=url_for('add_m'))

@app.route('/query',methods=["GET","POST"])
@login_required
def query():
    if request.method == 'GET':
        form = QueryForm()
    else:
        form = QueryForm(request.form)
        if form.validate():
            send = Sender()
            form.populate_obj(send)
            now = datetime.now()
            send.meeting_day = now.strftime("%Y%m%d")
            send.start_time = now.strftime("%H:%M:%S")
            send.volume = 1
            send.code = "600000"
            send.shorsz = "XSHG"
            send.price = 1.00
            tmp_code = f"{send.code}.{send.shorsz}"
            tmp_price = float(send.price)
            logging.info(f"{send.type} {send.stg}")
            db.session.add(send)
            db.session.commit()
            message_data = {
                'code': tmp_code,
                'amt': send.volume, 
                'type': send.type, 
                'price': tmp_price, 
                'stg': send.stg      
            }
            try:
                rds = get_redis_connection()
                rds.xadd("order", message_data)
            except Exception as e:
                logging.error(f'redis连接失败,正在尝试重连{e}')
            return redirect(url_for('query'))
        else:
            logging.error(f"错误信息:{form.errors}")
    return render_template('sample_query.htm', list1=[
        ('当天发送列表', url_for('v_list')),
        ('添加会议', url_for('add_m')),
        ('添加查询', url_for('query')),
        ('当天接受列表', url_for('query_m'))
    ], form=form, link=url_for('query'))


@app.teardown_request
def teardown(exception):
    global is_start
    if not is_start:
        time.sleep(20)
        logging.info("退出程序")
        os._exit(0)


if __name__ == "__main__":
    av1 = len(sys.argv) > 1
    get_msg = Msg()
    if av1:
        get_msg.xgroup_create()
        username = input("username:")
        password = input("password:")
        with app.app_context():
            db.drop_all()
            db.create_all()  # make our sqlalchemy tables
            admin = Admin(username=username, password=password)
            db.session.add(admin)
            db.session.commit()
        logging.info("数据库创建成功")

    else:
        logging.info("启动后台服务")
        get_msg.start_background()
        app.run(host='0.0.0.0',port=8001)