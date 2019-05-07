import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# 使用dotenv工具导入环境变量
# 有些配置信息，如SECRET_KEY、DATABASE_URL等，不方便放在config.py中，
# 这种信息放到一个额外的.env文件中，这个文件由dotenv工具导入
# 不应该将*.env加入到源代码版本控制中，因为这样不安全！
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
            'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 添加电子邮件信息，用于在发生错误后自动发送电子邮件通知
    # 如果环境中没有电子邮件功能，则不会启动
    # 默认使用python自带的一个模拟电子邮件服务器
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or '127.0.0.1'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']

    # 分页，配置每页展示的数据列表长度
    POSTS_PER_PAGE = 3

    # 国际化
    LANGUAGES = ['zh_CN', 'en', 'es']

    # 微软翻译API，实际上我没有注册，所以这块不生效，实际需要使用时，要设置环境变量
    # 然而这个环境变量里边的key值是保密的，所以不应该卸载config.py中，下边声明的变量应该写在.env文件中，并不要包含在源代码管理中
    # export MS_TRANSLATOR_KEY=<paste-your-key-here>
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY') or None

    # 添加全局搜索引擎的URL，使用elasticsearch
    # 需要安装elasticsearch软件，在MacOS上是：brew install elasticsearch
    # 还需要安装python的elasticsearch客户端工具包
    # 我这里写为获取环境变量值，否则为None，也就是不启动该功能，这个值是elasticsearch的默认端口
    # 需要在.env中设置环境变量的值：ELASTICSEARCH_URL=http://localhost:9200
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or None

    # Redis连接URL的配置
    # 如果环境变量未指定，则为本机默认端口和url
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
