from flask import jsonify, g
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth

# 获取token的路由函数
@bp.route('/tokens', methods=['POST'])
# 指定该路由函数必须先经过basic_auth验证身份，凭证有效后才能够获取token
# 需要注意，basic_auth验证和token_auth是两种方式，token_auth需要token的支持，
# 而token的获取依然需要basic_auth，也就是用户名和密码的验证
@basic_auth.login_required
def get_token():
    # 如果凭证有效，则使用get_token生成一个token
    token = g.current_user.get_token()
    # 需要将token和过期时间写回到数据库
    db.session.commit()
    return jsonify({'token': token})

# 发送delete请求后使现有token失效
@bp.route('/tokens', methods=['DELETE'])
# 这里使用token验证通过后才允许访问
@token_auth.login_required
def revoke_token():
    # 使用user模型中的辅助方法实现撤销token
    g.current_user.revoke_token()
    db.session.commit()
    # 返回码204的意义是成功请求却没有响应主体的响应
    return '', 204
