from flask_mail import Message
from flask import render_template
from app import mail, app
from threading import Thread
from flask_babel import _

# 异步发送邮件
# 参数app是将上下文传递到线程中
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# 修改为启动一个线程，异步发送邮件
def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    #mail.send(msg)
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    # 提供txt和html两种版本的邮件格式，适应不同的客户端
    send_email(_('[Microblog] Reset Your Password'),
            sender=app.config['ADMINS'][0],
            recipients=[user.email],
            text_body=render_template('email/reset_password.txt', user=user, token=token),
            html_body=render_template('email/reset_password.html', user=user, token=token))
