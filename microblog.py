from app import app, db
from app.models import User, Post

# 为flask shell命令准备的上下文
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}

# if __name__ == "__main__":
    # app.run('127.0.0.1', port=5000, ssl_context=('cert.pem', 'key.pem'))
    # app.run('127.0.0.1', port=5000)

