import threading
from time import sleep
from app import create_app
from app.logging_config import logger
from app.tasks import monitor_redis

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

def post_fork(server, worker):
    if worker.is_main:
        start_monitor_redis()