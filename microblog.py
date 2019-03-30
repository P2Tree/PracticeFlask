from app import app, db
from app.models import User, Post

# 为flask shell命令准备的上下文
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}
