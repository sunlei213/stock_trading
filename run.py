import sys
import threading
from time import sleep
from app import create_app, db, get_redis_client
from app.models import Admin
from app.logging_config import logger
from app.tasks import monitor_redis, stop_scheduler
import atexit

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

if __name__ == '__main__':
    # 注册退出时的清理函数
    atexit.register(stop_scheduler)
    
    av1 = len(sys.argv) > 1
    if av1:
        with app.app_context():
            redis_client = get_redis_client()
            redis_client.xgroup_create()
            username = input("username:")
            password = input("password:")
            db.drop_all()
            db.create_all()
            admin = Admin(username=username, password=password)
            db.session.add(admin)
            db.session.commit()
        logger.info("数据库创建成功")

    else:
        logger.info("启动后台服务")
        threading.Thread(target=start_monitor_redis, daemon=True).start()
        app.run(host='0.0.0.0',port=8001)
