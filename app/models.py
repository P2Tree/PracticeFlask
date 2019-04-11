from datetime import datetime
from time import time

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import app

from hashlib import md5
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired

import jwt

# 用户粉丝，使用多对多关系，并且是自引用关系，以下建立一个关联表
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')),
                     )

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # 表间的高级映射，这里是一对多关系，user是一，post是多
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # 粉丝
    followed = db.relationship(
        'User', # 关联表右侧实体，是被关注的一方，左侧实体，即关注者，是其上级实体
        secondary=followers,    # 指定用于该关系的关联表
        primaryjoin=(followers.c.follower_id == id),    # 通过关联表关联到左侧实体（关注者）的条件
        secondaryjoin=(followers.c.followed_id == id),  # 通过关联表关联到右侧实体（被关注者）的条件
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic' # 指定右侧实体如何访问关系
    )


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

    # 关注用户
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    # 取消关注用户
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    # 检查是否已关注
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0 # 这里使用count是教学需要，实际上只会返回0或1

    # 查询所有关注用户的动态，并按条件返回信息
    def followed_posts(self):
        # 条件查询操作+条件过滤，查找关注的用户的动态并排序
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        # 查找自己的动态
        own = Post.query.filter_by(user_id=self.id)
        # 将两者结合起来，并排序
        return followed.union(own).order_by(Post.timestamp.desc())

    # 获取重置密码的token，token过期时间是10分钟
    def get_reset_password_token(self, expires_in=600):
        # 加密秘钥是config中的SECRET_KEY，token的字段由一个用户id和一个过期时间组成
        # 注意到，这个encode中的参数algorithm不带s
        # utf-8是必须的，因为encode会按照字节序列返回，而在应用中，使用字符串更方便
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},
                        app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # 验证重置密码的token
    @staticmethod
    def verify_reset_password_token(token):
        try:
            # 注意到，这个decode中的参数algorithms带s
            # decode验证不通过会触发异常，所以放到try中
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        # 获取到提取id对应的用户
        return User.query.get(id)

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

