import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'A0Zrk8j/3yX4R~XHH!jmN]LWX/,?RT' # 用于Flask-Login的密钥
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = 'logs/app.log'
    LOG_LEVEL = 'INFO'
    ENABLE_MONITORING = False #是否启用性能监控
    ENABLE_PROFILING = False #是否启用性能分析
    LOG_FILE_MAX_SIZE = 1024 * 1024 * 5 #日志文件最大大小，单位为字节, 默认为5M
    LOG_FILE_BACKUP_COUNT = 2 #日志文件备份数量
    TDX_HOST = 'shtdx.gtjas.com'

class redisConfig:
    host = 'redis-12870.c302.asia-northeast1-1.gce.redns.redis-cloud.com'
    port = 12870
    pwd = 'gqdTByOKjOlWIjAKyI18WyuZOUQYbifx'
    msg_stream_name = "msg"  # 订单消息流
    msg_consumer_group = "msg_group"  # 订单消息消费组
    msg_consumer_name = "msg_consumer"  # 订单消息消费者
    order_stream_name = "order" 
    order_consumer_group = "order_msg_group" 
    order_consumer_name = "order_msg_consumer" 