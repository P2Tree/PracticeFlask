from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth

app = Flask(__name__)

app.config.from_object(Config) #获取配置项类

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login' # 向Flask-Login指定login视图函数用于处理登陆认证

# 为API请求准备的授权验证方式
auth = HTTPBasicAuth()

from app import routes, models #放到底部，避免循环导入

