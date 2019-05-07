import time
from rq import get_current_job
from app import create_app, db
from app.models import Task, User, Post
import sys
import json
from flask import render_template
from app.email import send_email

# 任务是一个独立于flask进程的进程，从而需要新建app实例来引用一些flask中的功能，如访问数据库和发送电子邮件等
app = create_app()
# 需要获取app的上下文
app.app_context().push()

# 用于向客户端推送任务进度的辅助函数
def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        # 使用user模型已有的add_notification方法来将通知发送到请求任务的用户
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True

        # 确保父任务不执行任何数据库更改，如果更改，则这里会将父任务的更改也提交
        db.session.commit()

# 导出用户动态任务的结构
def export_posts(user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(0)
        data = []
        i = 0
        total_posts = user.posts.count()

        # 按时间顺序索引
        for post in user.posts.order_by(Post.timestamp.asc()):
            # 返回json格式的列表
            # 'Z'表示时区为UTC
            data.append({'body': post.body,
                        'timestamp': post.timestamp.isoformat() + 'Z'})
            # 这个延时的作用只是方便调试时能看到进度变化，以防日志不多时看不到现象
            time.sleep(1)

            i += 1
            # //表示整除，向下取整
            _set_task_progress(100 * i // total_posts)

        # 采用同步方式发送邮件
        # 使用json.dumps函数生成一个json串
        send_email('[Microblog] Your blog posts',
                   sender=app.config['ADMINS'][0], recipients=[user.email],
                   text_body=render_template('email/export_posts.txt', user=user),
                   html_body=render_template('email/export_posts.html', user=user),
                   attachments=[('posts.json', 'application/json',
                                 json.dumps({'posts': data}, indent=4))],
                   sync=True)
    except:
        _set_task_progress(100)
        # 使用flask的日志记录器来记录错误
        # 其中sys.exc_info()用来获取堆栈跟踪信息
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
        # handle unexpected errors
