from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config) #获取配置项类

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models #放到底部，避免循环导入
