from apscheduler.schedulers.background import BackgroundScheduler
from app import db, redis_client
from app.models import Account, Order, Trade
import threading

scheduler = BackgroundScheduler()

def query_account_funds():
    """每 20 秒查询账户资金"""
    redis_client.send_command('order', 'query_account_funds')

def query_orders_and_trades():
    """每 20 秒查询委托和成交"""
    redis_client.send_command('order', 'query_orders_and_trades')

def start_scheduler():
    """启动定时任务"""
    scheduler.add_job(query_account_funds, 'interval', seconds=20)
    scheduler.add_job(query_orders_and_trades, 'interval', seconds=20)
    scheduler.start()

def monitor_redis():
    """监控 Redis Stream 返回的结果"""
    last_id = '0'  # 从最新的消息开始读取

    while True:
        messages = redis_client.read_messages('msg', last_id)
        if messages:
            for stream, message_list in messages:
                for message_id, message in message_list:
                    last_id = message_id  # 更新最后读取的消息 ID
                    data = message[b'data'].decode('utf-8').split(',')
                    if data[0] == 'account_funds':
                        account = Account.query.filter_by(user_id=int(data[1])).first()
                        account.balance = float(data[2])
                        db.session.commit()
                    elif data[0] == 'order_confirmation':
                        order = Order.query.get(int(data[1]))
                        order.status = data[2]
                        db.session.commit()
                    elif data[0] == 'trade_execution':
                        trade = Trade(user_id=int(data[1]), stock_symbol=data[2], quantity=int(data[3]), price=float(data[4]))
                        db.session.add(trade)
                        db.session.commit()

# 启动定时任务和监控线程
start_scheduler()
threading.Thread(target=monitor_redis, daemon=True).start()