from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_httpauth import HTTPTokenAuth, HTTPBasicAuth
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_babel import lazy_gettext as _l

import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login' # 向Flask-Login指定login视图函数用于处理登陆认证
login.login_message = _l('Please log in to access this page.')
auth = HTTPBasicAuth() # 为API请求准备的授权验证方式
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel() # 国际化翻译工具

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class) #获取配置项类

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)


    from app.errors import bp as errors_bp # 放到这里，避免循环依赖
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    # url_prefix是指定这个blueprint中的路由的总前缀

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])

            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()

            mail_handler = SMTPHandler(
                    mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                    fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                    toaddrs=app.config['ADMINS'],
                    subject='Microblog Failure',
                    credentials=auth,
                    secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

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

    return app


@babel.localeselector
def get_locale():
    # 解析请求中的accept_languages头部表，内含浏览器希望的语言的权重，best_match是选取最佳的匹配语言
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])
    # 强制指定语言，不能带国家，比如中文，不能写zh_CN，只能写zh
    #return 'zh'

# 注册到Flask中的模块
from app import models #放到底部，避免循环导入

