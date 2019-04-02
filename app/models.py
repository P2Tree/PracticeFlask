from datetime import datetime

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import app

from hashlib import md5
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # 表间的高级映射，这里是一对多关系，user是一，post是多
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # 调试时打印输出
    def __repr__(self):
        return '<User {}>'.format(self.username)

    # 计算明文密码的hash密码
    def set_password(self, password):
        self.password_hash = generate_password_hash(password=password)

    # 校验明文密码与hash密码是否一致
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 该函数可以通过传入的邮件名称来从gravatar获取一个头像
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    # 为API授权登陆提供的TOKEN生成接口
    def generate_auth_token(self, expiration: object = 600) -> object:
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({ 'id': self.id })

    # 为API授权登陆提供的TOKEN验证接口
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # 验证成功，但token已超时过期
        except BadSignature:
            return None # 验证失败

        # 验证成功，获取用户信息
        user = User.query.get(data['id'])
        return user

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

