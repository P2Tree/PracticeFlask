from flask import request, jsonify, g, jsonify
from flask import render_template, flash, redirect, url_for, current_app
from app.main.forms import EditProfileForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message
from app.translate import translate
from flask_login import current_user, login_required
from app import db
from datetime import datetime
import base64
from flask_babel import _, get_locale
from guess_language import guess_language
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        # UTC时间
        current_user.last_seen = datetime.utcnow()

        # 在调用current_user时，flask-login已经自动将current_user添加到数据库会话，
        # 所以不需要写db.session.add()
        db.session.commit()

        # 指定一个全局的搜索表单，这个表单放在这里，可以保证对每个请求和每个客户端都是独立的
        g.search_form = SearchForm()

    # 国际化，设置语言
    g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        # 自动监测提交的post内容是什么语言
        language = guess_language(form.post.data)
        # 如果监测失败，则设置为空
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live'))
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int) # 如果没有page参数，则默认page变量为1

    # paginate是分页查询的方法
    # False表示如果未查询到，则返回空列表，如果改成True，如果未查询到，则返回404
    posts = current_user.followed_posts().paginate(
            page, current_app.config['POSTS_PER_PAGE'], False) 

    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None

    # posts现在是一个paginate对象，所以需要调用它的items成员，才是筛选出来的数据列表
    # 如果使用的是posts = current_user.followed_posts().all()，则只能一次性提取所有的动态，
    # 当动态量比较大时，会很耗时，all()返回的就是一个列表，没有items成员
    return render_template('index.html', title=_('Home Page'), form=form, posts=posts.items,
                            next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit(): # 如果验证成功，则是正确提交的内容，直接存入数据库
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET': # 如果是GET请求，则是第一次请求，获取默认的内容并返回页面输入
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    # 否则，验证失败且是POST请求，则直接返回原页面重新输入
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        #flash('User {} not found.'.format(username))
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    #flash('You are following {}!'.format(username))
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('main.user', username=username))

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        #flash('User {} not found.'.format(username))
        flash(_('User %(username)s not found', username=username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    #flash('You are not following {}.'.format(username))
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('main.user', username=username))

# 新建一个发现页面
@bp.route('/explore')
@login_required
def explore():
    # 该页面展示所有的动态
    page = request.args.get('page', 1, type=int)
    # 分页机制，查询动态内容
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None

    # 重用了index页面
    return render_template('index.html', title=_('Explore'), posts=posts.items,
                            next_url=next_url, prev_url=prev_url)

# 翻译文本的ajax请求响应
@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    # 这里的POST请求并不是表单数据，所以不能用Flask-WTF来解析，只能通过requests。form来获取
    # jsonify用来将字典转换为JSON格式的有效载荷
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})

# 全局搜索
@bp.route('/search')
@login_required
def search():
    # 不能用form.validate_on_submit来验证GET请求，因为没有submit
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    # 获取搜索结果列表
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    # 处理分页
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user_popup.html', user=user)

# 私有消息发送函数
@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)

# 私有消息查看消息函数
@bp.route('/messages')
@login_required
def messages():
    # 用于标记已读消息
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)



