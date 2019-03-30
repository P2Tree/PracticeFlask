from flask import request
from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm, RegistrationForm
from app.models import User
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app import db

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': "yangliuming"}
    posts = [
        {
            'author': {'username': 'xiaohan'},
            'body': 'Beatiful day in China'
        },
        {
            'author': {'username': 'hanxiaohan'},
            'body': 'The Avengers movie was so cool'
        }
    ]
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
