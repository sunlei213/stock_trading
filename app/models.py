from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    usedmoney = db.Column(db.Float, default=0.0)
    getmoney = db.Column(db.Float, default=0.0)
    stocksvalue = db.Column(db.Float, default=0.0)
    totlemoney = db.Column(db.Float, default=0.0)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_code = db.Column(db.String(6), nullable=False)
    stock_name = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    usedstock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    now_price = db.Column(db.Float, nullable=False)
    loss = db.Column(db.Float, nullable=False)
    loss_per = db.Column(db.Float, nullable=False)
    lock_quantity = db.Column(db.Integer, nullable=False)
    buy_quantity = db.Column(db.Integer, nullable=False)
    sell_quantity = db.Column(db.Integer, nullable=False)


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    send_day = db.Column(db.String(8), nullable=False)
    start_time = db.Column(db.String(8), nullable=False)
    stock_code = db.Column(db.String(6), nullable=False)
    stock_name = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(8), nullable=False)
    price = db.Column(db.Float, nullable=False)   
    volume = db.Column(db.Integer, nullable=False)
    no = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price1 = db.Column(db.Float, nullable=False)
    shorsz = db.Column(db.String(4))

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError(f'password是只读属性')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

class Sender(db.Model):
    """A single meeting"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meeting_day = db.Column(db.String(8))
    start_time = db.Column(db.String(8))
    code = db.Column(db.String(6))
    shorsz = db.Column(db.String(4))
    price = db.Column(db.DECIMAL(10,3))
    volume = db.Column(db.Integer)
    type = db.Column(db.String(8))


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))