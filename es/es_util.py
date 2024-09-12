# 用来创建es的两个index
from es import es_mappings
from Utils.util import validate_cve_id
from Constants.dbConstants import es

collection_index = {'merged_cve'}


def establish_es_index():
    for index_name in collection_index:
        # 如果已经存在索引，照常使用
        if es.indices.exists(index=index_name):
            print(f"Already exists index: {index_name}")
            return
        if index_name == 'merged_cve':
            create_index_response = es.indices.create(index=index_name, body={
                "mappings": es_mappings.nvd_mappings
            })
            print(create_index_response)
        else:
            print("UNSUPPORTED INDEX NAME!!")


def search_by_cve_id(cve_id):
    cve_id = cve_id.upper()
    # 不是有效的cve-id
    if not validate_cve_id(cve_id):
        return {
            'code': 500,
            'message': 'cve格式不正确！',
            'data': None
        }
    body = {
        "query": {
            "term": {
                "No": cve_id
            }
        }
    }
    return search_by_query(body)


def search_by_query(body):
    index_name = 'merged_cve'
    try:
        result = es.search(index=index_name, body=body)
    except Exception as e:
        print("es搜索出现异常：{},{}".format(e, e.__traceback__))
        return {
            'code': 500,
            'message': 'es搜索出现异常',
            'data': None
        }
    print("query data: ", result)
    hits = result["hits"]["hits"]
    return {
        'code': 200,
        'message': '成功',
        'data': hits[0]["_source"] if hits else None
    }
