from flask import Blueprint

bp = Blueprint('errors', __name__)

# 放到结尾，避免循环依赖
from app.errors import handlers
