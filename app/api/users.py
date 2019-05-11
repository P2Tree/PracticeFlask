from app.api import bp
from flask import jsonify, request, url_for
from app.models import User
from app import db
from app.api.errors import bad_request
from app.api.auth import token_auth


# 获取一个用户
@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    # 使用to_dict方法将返回的User模型转换为一个字典格式，然后用jsonify格式化为json串
    return jsonify(User.query.get_or_404(id).to_dict())


# 获取所有用户
@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    # 如果请求中不存在当前页码，默认值为1
    page = request.args.get('page', 1, type=int)
    # 如果请求中不存在每页项数，则默认值为10，另外设置最大值是100
    # per_page过大可能会导致服务器性能问题
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    # 使用to_collection_dict方法收集用户群的信息，并分页
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)


# 获取某个用户的粉丝
@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    # to_collection_dict中需要指定id参数，用来指定特定用户
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)


# 获取某个用户关注的用户
@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
    return jsonify(data)

# 创建一个用户
# 创建一个用户不需要token认证，用户还未存在时没有token
@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    # 当new_user=True时，将会接收password字段
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201 # 201是创建新实体成功后的返回代码
    # HTTP协议要求201响应需包含一个值为新资源url的Location头部
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

# 更新一个用户
@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    # 如果字段中存在用户名（请求是在修改用户名）且用户名和当前的不一样，然后修改的
    # 用户名在已有数据库中不存在，如果不满足则返回错误
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
        User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())


