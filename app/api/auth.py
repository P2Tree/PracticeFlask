from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app.models import User
from app.api.errors import error_response

# 使用Flask-HTTPAuth插件实现token认证功能
# 需要安装该插件 pip install flask-httpauth
basic_auth = HTTPBasicAuth()

token_auth = HTTPTokenAuth()

# 用于验证用户用户名和密码的函数，注册到basic_auth中用来验证时调用
@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        # 告诉httpauth凭证无效
        return False
    # 将认证通过的用户保存在current_user中
    g.current_user = user
    # 依然使用check_password来验证密码，这是在模板中自定义的一个辅助函数
    # 如果返回True，则httpauth认为凭证有效
    return user.check_password(password)

# 用于在认证失败时返回的错误响应，注册到basic_auth中用来当验证失败时的返回调用
@basic_auth.error_handler
def basic_auth_error():
    # 错误码401是未授权的意思，客户端收到401后即可知道需要重新发送有效的凭证
    return error_response(401)

# 验证token的函数，注册到token_auth中用来验证时调用
@token_auth.verify_token
def verify_token(token):
    # 使用check_token方法来验证token的有效性，该方法是在User模型中定义的一个辅助函数
    # 当token缺失时，会将当前用户token字段设置为None
    g.current_user = User.check_token(token) if token else None
    # 返回值是True或False会决定Flask-HTTPAuth是否允许视图函数运行
    return g.current_user is not None

# 验证token失败后的错误响应，注册到token_auth中用来验证失败时返回调用
@token_auth.error_handler
def token_auth_error():
    return error_response(401)
