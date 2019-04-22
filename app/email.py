from flask_mail import Message
from app import mail
from flask import current_app
from threading import Thread

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

    # 这种发送是同步的发送
    #mail.send(msg)

    # 这种是异步发送
    # current_app变量是一个代理变量，该变量在传递到另一个线程中后，在另一个线程中不会有效，
    # 所以需要使用_get_current_object()方法，提取代理变量的实际实例，然后传入
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
