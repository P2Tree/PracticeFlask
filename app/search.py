from flask import current_app

# 这些方法将在app/models.py中的SearchableMixin类中被调用
# 不应该手动去调用

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)

    # elasticsearch支持的添加索引函数
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id, body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return

    # elasticsearch支持的删除索引函数
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0

    # elasticsearch支持的搜索函数
    # 支持分页功能
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        body={'query':{'multi_match': {'query':query, 'fields':['*']}},
              'from':(page -1)*per_page, 'size':per_page})
    # search['hits']['hits']这种用法是python的一个特性，叫列表推导式
    ids = [int(hit['_id']) for hit in search['hits']['hits']]

    # 返回两个值，第一个是所有匹配的结果的id元素的列表，第二个是匹配到的总数
    return ids, search['hits']['total']

def remove_all(index):
    if not current_app.elasticsearch:
        return

    current_app.elasticsearch.indices.delete(index)
