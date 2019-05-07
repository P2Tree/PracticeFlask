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
# attachments是一个元组列表，每个元组为3个参数，第1个参数是附件名称，
# 第2个参数是媒体类型（如image/png或application/json），第3个参数是附件内容（字符串或字节序列）
# sync参数将会控制是否选择同步模式发送
def send_email(subject, sender, recipients, text_body, html_body,
               attachments=None, sync=False):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            # Flask-Mail支持的默认附件功能
            # 使用*attachment来将元组中的三个参数解包成attach函数的三个参数后传入attach
            # 如果没有*号，则会传入一个元组数据，这样对于attach函数来说是不正确的
            msg.attach(*attachment)

    if sync:
        # 这种发送是同步的发送
        mail.send(msg)
    else:
        # 这种是异步发送
        # current_app变量是一个代理变量，该变量在传递到另一个线程中后，在另一个线程中不会有效，
        # 所以需要使用_get_current_object()方法，提取代理变量的实际实例，然后传入
        Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
