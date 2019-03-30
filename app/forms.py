from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField # 引入表单字段
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()]) # DataRequired()验证器仅验证输入是否为空
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
