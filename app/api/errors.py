from flask import jsonify
# HTTP_STATUS_CODES是一个字典，为每一个http错误代码准备了一个简短的描述性内容
from werkzeug.http import HTTP_STATUS_CODES


# 当发生一个错误请求时，返回API的状态码为400的错误响应
def bad_request(message):
    return error_response(400, message)


# 返回API的错误
def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message

    # jsonify会创建一个状态码为200的默认response对象，负载是我们准备的
    response = jsonify(payload)
    # 然后我们将这个response对象中的状态码修改为实际的错误代码
    response.status_code = status_code
    return response
