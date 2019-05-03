from datetime import datetime
from time import time

from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app

from hashlib import md5
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired

import jwt
from app.search import add_to_index, remove_from_index, query_index, remove_all

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

    # 支持私有消息
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

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
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({ 'id': self.id })

    # 为API授权登陆提供的TOKEN验证接口
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
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
                        current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # 验证重置密码的token
    @staticmethod
    def verify_reset_password_token(token):
        try:
            # 注意到，这个decode中的参数algorithms带s
            # decode验证不通过会触发异常，所以放到try中
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        # 获取到提取id对应的用户
        return User.query.get(id)

    # 私有消息功能辅助函数，返回用户有多少条未读私有消息
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()

# 为了保证数据库变化时自动触发elasticsearch索引动作，而设计的一个mixin类
# 从而通过SQLAlchemy的事件机制来触发elasticsearch的动作
# app/search.py中的方法不能外部调用，因为可能会导致数据库和搜索索引内容不一致
# 这些方法在mixin类中被同步调用
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        # 返回结果ID列表和总数
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            # 使用case语句，确保数据库中的结果与给定ID的顺序相同
            # 因为使用elasticsearch搜索返回的结果不是有序的
            db.case(when, value=cls.id)), total

    # 在before_commit中保存需要处理的数据，这个事件是在SQLAlchemy提交操作之前触发
    # 在SQLAlchemy提交之后，将需要保存的数据更新elasticsearch
    # 这么做的原因就是SQLAlchemy可能提交失败，对数据的完整性有保障
    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': [obj for obj in session.new if isinstance(obj, cls)],
            'update': [obj for obj in session.dirty if isinstance(obj, cls)],
            'delete': [obj for obj in session.deleted if isinstance(obj, cls)]
        }

    # SQLAlchemy提交之后，将before_commit中保存的数据更新elasticsearch
    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['update']:
            add_to_index(cls.__tablename__, obj)
        for obj in session._changes['delete']:
            remove_from_index(cls.__tablename__, obj)
        session._changes = None

    # 一个辅助函数，能够将表中所有的内容添加到搜索索引中
    # 通过执行Post.reindex()即可
    @classmethod
    def reindex(cls):
        for obj in cls.query:
            print("Add Post: <" + str(obj.id) + " " + obj.body + "> into " + cls.__tablename__)
            add_to_index(cls.__tablename__, obj)

    # 一个辅助函数，能够删除该表的所有索引
    @classmethod
    def delete_index(cls):
        remove_all(cls.__tablename__)


# 第一个继承的类，用于指定Post表更新时的触发事件
class Post(SearchableMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    language = db.Column(db.String(5))

    # 用于使能搜索的标志
    # 指定搜索的字段是body
    __searchable__ = ['body']

    def  __repr__(self):
        return '<Post {}>'.format(self.body)


# 注册Post的事件处理函数
db.event.listen(db.session, 'before_commit', Post.before_commit)
db.event.listen(db.session, 'after_commit', Post.after_commit)


# 为Flask-Login准备的辅助加载用户的函数
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# 支持私有消息功能
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 发件人
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # 收件人
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    # 最后一次阅读私有消息的时间
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())

    def __repr(self):
        return '<Message {}>'.format(self.body)
