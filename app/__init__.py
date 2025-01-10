from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from redis import Redis
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
redis = Redis.from_url(Config.REDIS_URL)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app import routes
    app.register_blueprint(routes.bp)

    return app