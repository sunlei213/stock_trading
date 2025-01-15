import threading
from time import sleep
from app import create_app
from app.logging_config import logger
from app.tasks import monitor_redis, get_msg_queue

# 绑定地址和端口
bind = "0.0.0.0:8001"

# worker 数量
workers = 4

# worker 类型

# worker_class = "gthread"


# 线程数
# threads = 4 

# 性能调优
max_requests = 1000
max_requests_jitter = 50

# 日志配置

errorlog = "/root/stock_trading/logs/error.log"

app = create_app()

def start_monitor_redis():
    def run_monitor():
        with app.app_context():
            monitor_redis()

    t = threading.Thread(target=run_monitor, daemon=True)
    t.start()
    logger.info("启动redis监控线程")

    while True:
        sleep(30)
        if not t.is_alive():
            logger.error("redis监控线程异常退出")
            t = threading.Thread(target=run_monitor, daemon=True)
            t.start()


def child_msg_queue():
    run_once = get_msg_queue()
    run_once.start()
    while True:
        sleep(30)
        run_once.check_main_thread()

def when_ready(server):
    logger.info("启动后台服务")
    threading.Thread(target=start_monitor_redis, daemon=True).start()
    threading.Thread(target=child_msg_queue, daemon=True).start()


