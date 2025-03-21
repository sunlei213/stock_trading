import threading
from multiprocessing import  Queue
from queue import Full
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from app import db, get_redis_client
from app.models import User, Stock, Trade, Reciver
from app.logging_config import logger
from datetime import datetime


import re


class MessageType:
    def __init__(self): 
        self.process = {}
        self.process['CANCEL'] = self._process_cancel
        self.process['ORDER'] = self._process_order
        self.process['TRADE'] = self._process_trade
        self.process['POSITION'] = self._process_position
        self.process['BALANCE'] = self._process_balance
        self.stk_code_pattern = re.compile(r'(\d{6})')

    def _process_cancel(self, user_id, data):
        return f'取消委托{data}'

    def _process_order(self, user_id, data):
        return f"委托， 委托号：{data.get('entrust_no', '0')},委托状态：{data.get('message', '正常')}"
    
    def _process_trade(self, user_id, msg):

        today = datetime.now().strftime("%Y%m%d")
        for trade in msg:
            match_res = self.stk_code_pattern.search(trade.get('证券代码'))
            if not match_res:
                continue
            code = match_res.group(1)
            record = Trade.query.filter_by(user_id=user_id, no=trade.get('委托编号'), send_day=today).first()
            if not record:
                record = Trade(
                    user_id=user_id, 
                    no=trade.get('委托编号'), 
                    send_day=today,
                    start_time=trade.get('委托时间', 'N/A'), 
                    stock_code=code, 
                    stock_name=trade.get('证券名称', 'N/A'), 
                    type=trade.get('买卖', 'N/A'),
                    price=trade.get('委托价格', 0.0), 
                    volume=trade.get('委托数量', 0),
                    price1=trade.get('成交价格', 0.0), 
                    volume1=trade.get('成交数量', 0),
                    return_vol=trade.get('撤单数量', 0), 
                    status=trade.get('委托状态', 'N/A'),
                    msg=trade.get('返回信息', 'N/A'), 
                    shorsz=trade.get('交易市场', 'N/A'))
                db.session.add(record)
                db.session.commit()
            record.status = trade.get('委托状态', 'N/A')
            record.msg = trade.get('返回信息', 'N/A')
            record.price1 = trade.get('成交价格', 0.0)
            record.volume1 = trade.get('成交数量', 0)
            record.return_vol = trade.get('撤单数量', 0)
            db.session.commit()
        return "委托查询"

    def _process_position(self, user_id, msg):

        updated_count = 0
        current_stock_codes = set()  # 用于存储当前持仓数据中的股票代码
        try:
            for stock in msg:
                match_res = self.stk_code_pattern.search(stock.get('证券代码',''))
                if not match_res:
                    continue
                code = match_res.group(1)
                current_stock_codes.add(code)
                record = Stock.query.filter_by(user_id=user_id, stock_code=code).first()
            # 创建新记录（如果不存在）
                if not record:
                    record = Stock(
                        user_id=user_id,
                        stock_code=code,
                        stock_name=stock.get('证券名称', 'N/A'),
                        quantity=0,
                        usedstock=0,
                        price=0.00,
                        now_price=0.00,
                        loss=0.00,
                        loss_per=0.00,
                        lock_quantity=0,
                        buy_quantity=0,
                        sell_quantity=0
                    )
                    db.session.add(record)
                    db.session.commit()
                record.quantity = int(stock.get('参考持股', '0'))
                record.usedstock = int(stock.get('可用股份', '0'))
                record.price = float(stock.get('成本价', '0.00'))
                record.now_price = float(stock.get('当前价', '0.00'))
                record.loss = float(stock.get('浮动盈亏', '0.00'))
                record.loss_per = float(stock.get('盈亏比例(%)', '0.00'))
                record.lock_quantity = int(stock.get('冻结股份', '0'))
                record.buy_quantity = int(stock.get('在途股份(买入成交)', '0'))
                record.sell_quantity = int(stock.get('卖出成交数量', '0'))
                db.session.commit()
                updated_count += 1

        except Exception as e:
            db.session.rollback()
            logger.error(f"处理股票 {code} 时出错: {str(e)}")

        # 第二步：删除不在当前持仓数据中的记录
        try:
            # 查询数据库中该用户的所有股票记录
            db_records = Stock.query.filter_by(user_id=user_id).all()

            # 遍历数据库记录，删除不在当前持仓数据中的记录
            for record in db_records:
                if record.stock_code not in current_stock_codes:
                    db.session.delete(record)
                    logger.info(f"删除股票记录: 用户 {user_id}, 股票代码 {record.stock_code}")

            # 提交删除操作
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除不在持仓数据中的记录时出错: {str(e)}")

        return f"持仓查询完成"

    def _process_balance(self, user_id, data):
        record = User.query.filter_by(id=user_id).first()
        if not record:
            record = User(
                id=user_id, 
                username=('孙克昆' if user_id == '536' else '谢爱琴'), 
                balance=0.00, 
                usedmoney=0.00, 
                getmoney=0.00, 
                stocksvalue=0.00, 
                totlemoney=0.00)
            db.session.add(record)
            db.session.commit()
        record.username = '孙克昆' if user_id == '536' else '谢爱琴'
        record.balance = float(data.get('资金余额', '0.00'))
        record.usedmoney = float(data.get('可用金额', '0.00'))
        record.getmoney = float(data.get('可取金额', '0.00'))
        record.stocksvalue = float(data.get('股票市值', '0.00'))
        record.totlemoney = float(data.get('总资产', '0.00'))
        db.session.commit()
        return f"金额：{data.get('可用金额', 'N/A')}, 市值:{data.get('股票市值', 'N/A')}, 总资产：{data.get('总资产', 'N/A')}"

message_type = MessageType()

class Msg_queue:
    def __init__(self):
        self.queue = None
        self.main_thread = threading.Thread(target=self.get_msg, daemon=True)
        self.threadpool = ThreadPoolExecutor(max_workers=10)
        # self.main_thread.start()

    def set_queue(self,queue):
        self.queue = queue

    def start(self):
        self.main_thread.start()

    def query_account_funds(self, user_id):
        """查询账户资金"""
        for _ in range(3):
            for msg_type in ['POSITION', 'BALANCE', 'TRADE']:
                try:
                    self.queue.put_nowait({'type': msg_type,'stg': user_id})
                except Full:
                    logger.error("消息队列已满")
                sleep(1)
            sleep(20)

    def check_main_thread(self):
        """检查主线程是否存活"""
        if not self.main_thread.is_alive():
            self.main_thread = threading.Thread(target=self.get_msg, daemon=True)
            self.main_thread.start()

    def get_msg(self):
        """获取消息并处理"""
        logger.info("消息队列线程启动")
        is_send = True
        while True:
            if not self.queue.empty():
                if is_send:
                    data = self.queue.get()
                if data:
                    if data.get('type') == 'aaa':
                        logger.info(f"开始查询线程")
                        self.threadpool.submit(self.query_account_funds, data.get('user_id'))
                        continue
                    try:
                        redis_client = get_redis_client()
                        if not redis_client:
                            logger.error("无法获取Redis客户端")
                            is_send = False
                            continue

                        if not redis_client.send_command(data):
                            logger.error(f"发送指令失败：{data}")
                            is_send = False
                            continue
                    except Exception as e:
                        logger.error(f"发送指令失败：{data}, 错误信息：{e}")
                        is_send = False
                        # 记录异常堆栈信息
                        logger.exception(e)
                    is_send = True
                else:
                    logger.info("消息队列线程退出")
                    break

global_queue = Queue()

msg_queue = Msg_queue()


def get_msg_queue():
    """获取消息队列实例"""
    global global_queue
    if not msg_queue.queue:
        msg_queue.set_queue(global_queue)
        logger.info('msg_queue设置队列')
    return msg_queue

def start_query(user_id):
    """开始查询"""
    global global_queue
    logger.info(f"开始查询线程")
    try:
        global_queue.put_nowait({'type': 'aaa', 'user_id': user_id})
    except Full:
        logger.error("消息队列已满")
    """
    if not self.main_thread.is_alive():
        self.main_thread = threading.Thread(target=self.get_msg, daemon=True)
        self.main_thread.start()
    self.threadpool.submit(self.query_account_funds, user_id)
    """

def send_msg(data):
    global global_queue
    logger.info(f"发送消息：{data}")
    try:
        global_queue.put_nowait(data)
    except Full:
        logger.error("消息队列已满")
    """
    if not self.main_thread.is_alive():
        self.main_thread = threading.Thread(target=self.get_msg, daemon=True)
        self.main_thread.start()
    """


def query_account_funds():
    """每 20 秒查询账户资金"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            logger.error("无法获取Redis客户端")
            return

        for stg in ["536", "537"]:
            for msg_type in ['BALANCE', 'POSITION']:
                if not redis_client.send_command({'type': msg_type, 'stg': stg}):
                    logger.error(f"发送{msg_type}指令失败")
                sleep(1)
    except Exception as e:
        logger.error(f"查询账户资金失败: {e}")
        # 记录异常堆栈信息
        logger.exception(e)

def query_orders_and_trades():
    """每 20 秒查询委托和成交"""
    redis_client = get_redis_client()
    for stg in ["536", "537"]:
        redis_client.send_command({'type': 'TRADE', 'stg': stg})
        sleep(1)

def _process_message(data):
    """处理消息"""
    if not data or 'type' not in data or 'ret' not in data:
        return None
    msg_type = data.get('type')
    ret = data['ret']
    try:
        msg = eval(data['msg']) if 'msg' in data else {}
    except (SyntaxError, ValueError, NameError):
        msg = data['msg'] if 'msg' in data else {}
    if ret == '1':
        if msg_type == 'BUY' or msg_type == 'SELL':
            msg_type = 'ORDER'
        if msg_type in message_type.process:
            return message_type.process[msg_type](data.get('stg'), msg)
        else:
            return f"未找到处理函数：{msg_type}{msg}"
    return f"委托失败信息：{msg}"

def _save_to_db(data, message):
    """保存到数据库"""
    now = datetime.now()
    today = now.strftime("%Y%m%d")
    now_time = now.strftime("%H:%M:%S")
    reci = Reciver(
        meeting_day = today,
        start_time = now_time,
        stg = data['stg'],
        type = data['type'],
        msg = message
    )
    db.session.add(reci)
    db.session.commit()
    return True

def monitor_redis():
    """监控 Redis Stream 返回的结果"""
    redis_client = get_redis_client()
    last_id = '0'  # 从最新的消息开始读取

    while True:
        messages = redis_client.read_group_messages()
        if messages and messages[0] and messages[0][1]:
            for message_list in messages[0][1]:
                message_id, data = __get_data(message_list)
                last_id = message_id
                if not data:
                    continue
                logger.info(f'消费到的数据 {data}')
                message = _process_message(data)
                if message:
                    _save_to_db(data, message)
                    redis_client.ack_message(last_id)

def __get_data(message_list):
    """解析消息数据"""
    if not message_list or not message_list[0]:
        return None, None
    msgId = message_list[0]
    data = {key: val for key, val in message_list[1].items()}
    return msgId, data

# 启动定时任务和监控线程
#start_scheduler()
#threading.Thread(target=monitor_redis, daemon=True).start()