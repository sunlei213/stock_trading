import os

class Config:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_POOL_SIZE = 10

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key' # 用于Flask-Login的密钥
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///stock_trading.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  