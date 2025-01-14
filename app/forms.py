from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField, SelectField, RadioField, DecimalField, IntegerField, PasswordField, DateField
from wtforms.validators import DataRequired
from wtforms.widgets import DateInput
import datetime

from wtforms.widgets import html_params



class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class OrderForm(FlaskForm):
    code = StringField(u'代码：', validators=[DataRequired()])
    code_select = SelectField(u'代码：', choices=[])
    price = DecimalField(u'价格：', validators=[DataRequired()])
    volume = IntegerField(u'数量：', validators=[DataRequired()])
    shorsz = RadioField(
        '市场：',
        validators=[DataRequired()],
        choices=[
            ('XSHG', '沪'),
            ('XSHE', '深')
        ]
    )
    type = SelectField(
        '委托方式：',
        validators=[DataRequired()],
        choices=[
            ('BUY', '买入'),
            ('SELL', '卖出')
        ]
    )
    # submit button will read "share my lunch!"
    submit = SubmitField(u'提交')

class QueryForm(FlaskForm):
    userid = RadioField(
        '账户：',
        validators=[DataRequired()],
        choices=[
            ('537', '主账户'),
            ('536', '备账户')
        ]
    )
    # submit button will read "share my lunch!"
    submit = SubmitField(u'提交查询')

class TaskForm(FlaskForm):
    submit = SubmitField('提交')

class TradeQueryForm(FlaskForm):
    start_date = DateField('起始日期',
                         format='%Y-%m-%d',
                         widget=DateInput(),
                         default=datetime.date.today(),
                         validators=[DataRequired()])
    end_date = DateField('终止日期',
                        format='%Y-%m-%d',
                        widget=DateInput(),
                        default=datetime.date.today(),
                        validators=[DataRequired()])
    user_id = SelectField('选择账户', coerce=int)