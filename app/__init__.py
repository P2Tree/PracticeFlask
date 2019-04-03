from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth

import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)

app.config.from_object(Config) #获取配置项类

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login' # 向Flask-Login指定login视图函数用于处理登陆认证

# 为API请求准备的授权验证方式
auth = HTTPBasicAuth()

# 启用文件日志功能
if not os.path.exists('logs'):
    os.mkdir('logs')
# 限制日志文件大小为10KB，同时只保留最后的10个日志文件作为备份
file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d'))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)

app.logger.setLevel(logging.INFO)
app.logger.info('Microblog startup')


# 注册到Flask中的模块
from app import routes, models, errors #放到底部，避免循环导入

