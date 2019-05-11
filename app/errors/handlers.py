from flask import render_template, request
from app import db
from app.errors import bp

from app.api.errors import error_response as api_error_response

# 如果不指定这些错误函数的返回值中的错误码，则默认是200，也就是成功

# http的内容协商判断
def wants_json_response():
    # 比较客户端对json和html的偏好程度
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']

@bp.app_errorhandler(404)
def not_found_error(error):
    # 根据http的内容协商结果，选择返回哪种格式的错误内容
    if wants_json_response():
        # 使用API接口中设计的错误返回，返回json格式内容
        return api_error_response(404)
    # 按照html格式渲染返回错误页面的
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    # 500错误一般会发生在数据库错误调用后，所以需要回滚数据库会话
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500
