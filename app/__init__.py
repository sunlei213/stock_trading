from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .redis_client import RedisClient
from config import Config, redisConfig
import logging

# 设置日志
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Config.LOG_FILE'),
        logging.StreamHandler()
    ]
)

logging.getLogger('werkzeug').setLevel(logging.ERROR)


db = SQLAlchemy()
login_manager = LoginManager()
logger = logging.getLogger(__name__)
# 全局 Redis 客户端实例
redis_client = RedisClient(host=redisConfig.host, port=redisConfig.port, db=0, password=redisConfig.pwd, max_connections=20)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # 指定未登录时重定向的视图函数
    login_manager.login_message = '请先登录!'
    login_manager.login_message_category = 'warning'

    from app import routes
    app.register_blueprint(routes.bp)

    return app