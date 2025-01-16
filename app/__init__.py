from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .redis_client import RedisClient
from config import Config, redisConfig
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.profiler import ProfilerMiddleware

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
# 全局变量声明
# 初始化Redis客户端
redis_client = RedisClient(
    host=redisConfig.host, 
    port=redisConfig.port,
    db=0,
    password=redisConfig.pwd,
    max_connections=20
)
redis_client.set_stream_name(
    redisConfig.msg_stream_name,
    redisConfig.msg_consumer_group,
    redisConfig.msg_consumer_name,
    redisConfig.order_stream_name
)


def get_redis_client():
    """获取 Redis 客户端实例"""
    return redis_client



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 确保设置了 SECRET_KEY
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = '请先登录!'
    login_manager.login_message_category = 'warning'
    
    # 注册蓝图
    from app import routes
    app.register_blueprint(routes.bp)
    
    # 添加性能监控
    if app.config.get('ENABLE_MONITORING', False):
        app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
            '/metrics': make_wsgi_app()
        })
        
        if app.config.get('ENABLE_PROFILING', False):
            app.wsgi_app = ProfilerMiddleware(
                app.wsgi_app,
                profile_dir='./profiles',
                restrictions=[30],
                sort_by=('cumulative', 'time', 'calls')
            )
    
    return app
