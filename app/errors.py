from flask import render_template
from app import app, db

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    # 500错误一般会发生在数据库错误调用后，所以需要回滚数据库会话
    db.session.rollback()
    return render_template('500.html'), 500

# 如果不指定这些错误函数的返回值中的错误码，则默认是200，也就是成功
