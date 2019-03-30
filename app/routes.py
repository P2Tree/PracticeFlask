from flask import render_template, flash, redirect
from app import app
from app.forms import LoginForm

@app.route('/')
@app.route('/index')
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
    return render_template('index.html', title='Home', user=user, posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit(): # GET请求是会返回false, 验证通过返回true
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)
