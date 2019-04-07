from flask import request, jsonify, g
from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
from app.models import User, Post
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from datetime import datetime
from app import auth
import base64

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()

        # 在调用current_user时，flask-login已经自动将current_user添加到数据库会话，
        # 所以不需要写db.session.add()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live')
        return redirect(url_for('index'))
    posts = current_user.followed_posts().all()
    return render_template('index.html', title='Home Page', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit(): # GET请求是会返回false, 验证通过返回true
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)

        # 跳转到上一个登陆前的页面，即next参数指定的页面
        next_page = request.args.get('next')
        # 检查next_page是否没有值，或者是否是绝对路径，如果满足任意一条，则跳转到主页
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Reigster', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post 1'},
        {'author': user, 'body': 'Test post 2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit(): # 如果验证成功，则是正确提交的内容，直接存入数据库
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET': # 如果是GET请求，则是第一次请求，获取默认的内容并返回页面输入
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    # 否则，验证失败且是POST请求，则直接返回原页面重新输入
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('Your are not following {}.'.format(username))
    return redirect(url_for('user', username=username))

# 新建一个发现页面
@app.route('/explore')
@login_required
def explore():
    # 该页面展示所有的动态
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    # 重用了index页面
    return render_template('index.html', title='Explore', posts=posts)


# 通过API获取token
@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii')})

# 通过API验证密码，两种验证，如果是token放到了username的位置，则只验证token，否则验证用户名和密码
@auth.verify_password
def verify_password(username_or_token, password):
    user = User.verify_auth_token(username_or_token)
    if not user:
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.check_password(password):
            return False
    g.user = user
    return True

# 通过API登陆
@app.route('/api/test_login')
@auth.login_required
def login_required():
    if g.user:
        return '<h1>you are still in</h1>'
    else:
        return '<h1>you have logouted</h1>'

