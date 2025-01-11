from flask_wtf import FlaskForm 
from wtforms.fields import StringField, SubmitField, SelectField, RadioField, DecimalField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(1, 128)])
    submit = SubmitField('登录')

class OrderForm(FlaskForm):
    code = IntegerField(u'代码：', validators=[DataRequired()])
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
