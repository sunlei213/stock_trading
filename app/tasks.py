from apscheduler.schedulers.background import BackgroundScheduler
from app import db, redis_client
from app.models import User, Stock, Trade, Reciver
from app.logging_config import logger
from datetime import datetime
import threading
import re

scheduler = BackgroundScheduler()

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
    
    def _process_trade(self, user_id, data):
        return f"成交， 委托号：{data.get('entrust_no', '0')}, 委托状态：{data.get('message', '正常')}"

    def _process_position(self, user_id, data):
        for stock in data:
            match_res = self.stk_code_pattern.search(stock.get('证券代码'))
            if not match_res:
                continue
            code = match_res.group(1)
            stock = Stock.query.filter_by(user_id=user_id, stock_code=code).first()
            if not stock:
                stock = Stock(user_id=user_id, stock_code=code, stock_name=stock.get('证券名称', 'N/A'), quantity=0, usedstock=0, price=0.00, now_price=0.00, loss=0.00, loss_per=0.00, lock_quantity=0, buy_quantity=0, sell_quantity=0)
                db.session.add(stock)
                db.session.commit()
            stock.quantity = int(data.get('参考持股', '0'))
            stock.usedstock = int(data.get('可用股份', '0'))
            stock.price = float(data.get('成本价', '0.00'))
            stock.now_price = float(data.get('最新价', '0.00'))
            stock.loss = float(data.get('浮动盈亏', '0.00'))
            stock.loss_per = float(data.get('盈亏比例(%)', '0.00'))
            stock.lock_quantity = int(data.get('冻结股份', '0'))
            stock.buy_quantity = int(data.get('在途股份(买入成交)', '0'))
            stock.sell_quantity = int(data.get('卖出成交数量', '0'))
            db.session.commit()
        return f"持仓查询"

    def _process_balance(self, user_id, data):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return f"用户不存在：{user_id}"
        user.balance = float(data.get('资金余额', '0.00'))
        user.usedmoney = float(data.get('可用金额', '0.00'))
        user.getmoney = float(data.get('可取金额', '0.00'))
        user.stocksvalue = float(data.get('股票市值', '0.00'))
        user.totlemoney = float(data.get('总资产', '0.00'))
        db.session.commit()
        return f"金额：{data.get('可用金额', 'N/A')}, 市值:{data.get('股票市值', 'N/A')}, 总资产：{data.get('总资产', 'N/A')}"

message_type = MessageType()

def query_account_funds():
    """每 20 秒查询账户资金"""
    redis_client.send_command('test', 'query_account_funds')

def query_orders_and_trades():
    """每 20 秒查询委托和成交"""
    redis_client.send_command('test', 'query_orders_and_trades')

def start_scheduler():
    """启动定时任务"""
    scheduler.add_job(query_account_funds, 'interval', seconds=20)
    scheduler.add_job(query_orders_and_trades, 'interval', seconds=20)
    scheduler.start()

def _process_message(data):
    """处理消息"""
    if not data or 'type' not in data or 'ret' not in data:
        return None
    msg_type = data.get('type')
    ret = data['ret']
    try:
        msg = eval(data['msg']) if 'msg' in data else {}
    except:
        msg = data['msg'] if 'msg' in data else {}
    if ret == 1:
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
    last_id = '0'  # 从最新的消息开始读取

    while True:
        messages = redis_client.read_group_messages('test_consumer', last_id)
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
                    redis_client.xack_message(last_id)


def stop_scheduler():
    """停止定时任务"""
    if scheduler.running:
        scheduler.shutdown()

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