import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'A0Zrk8j/3yX4R~XHH!jmN]LWX/,?RT' # 用于Flask-Login的密钥
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_FILE = 'app.log'
    LOG_LEVEL = 'INFO'

class redisConfig:
    host = 'redis-12870.c302.asia-northeast1-1.gce.redns.redis-cloud.com'
    port = 12870
    pwd = 'gqdTByOKjOlWIjAKyI18WyuZOUQYbifx'
    msg_stream_name = "test_msg"
    msg_consumer_group = "test_msg_group"
    msg_consumer_name = "test_msg_consumer"
    order_stream_name = "order_msg"
    order_consumer_group = "order_msg_group"
    order_consumer_name = "order_msg_consumer"