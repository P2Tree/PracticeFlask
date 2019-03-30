from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # 表间的高级映射，这里是一对多关系，user是一，post是多
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # 调试时打印输出
    def __repr__(self):
        return '<User {}>'.format(self.username)

    # 计算明文密码的hash密码
    def set_password(self, password):
        self.password_hash = generate_password_hash(password=password)

    # 校验明文密码与hash密码是否一致
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def  __repr__(self):
        return '<Post {}>'.format(self.body)

# 为Flask-Login准备的辅助加载用户的函数
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

