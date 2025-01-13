from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .redis_client import RedisClient
from config import Config, redisConfig



db = SQLAlchemy()
login_manager = LoginManager()

# 全局 Redis 客户端实例
redis_client = RedisClient(host=redisConfig.host, port=redisConfig.port, db=0, password=redisConfig.pwd, max_connections=20)
redis_client.set_stream_name(redisConfig.msg_stream_name, redisConfig.msg_consumer_group, redisConfig.msg_consumer_name, redisConfig.order_stream_name)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # 指定未登录时重定向的视图函数
    login_manager.login_message = '请先登录!'
    login_manager.login_message_category = 'warning'


    from app import routes
    app.register_blueprint(routes.bp)

    return app