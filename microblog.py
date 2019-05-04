from app import create_app, db
from app.models import User, Post, Notification, Message
import os

# 自己写的命令
from app import cli

# 在整个应用的入口初始化app实例，在后续的代码中只需要调用current_app就可以表示这个实例
app = create_app()

# 注册用于翻译的一些命令，在cli.py中定义
cli.register(app)

# 为flask shell命令准备的上下文
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Message': Message,
            'Notification': Notification}

# if __name__ == "__main__":
    # app.run('127.0.0.1', port=5000, ssl_context=('cert.pem', 'key.pem'))
    # app.run('127.0.0.1', port=5000)

