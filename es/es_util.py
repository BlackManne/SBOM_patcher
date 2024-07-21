# 用来创建es的两个index
from elasticsearch import Elasticsearch
import es_mappings
from es.dbTransfer import transfer_to_es
from Utils.util import validate_cve_id

collection_index = {'nvd'}


def establish_es_index():
    # 连接到Elasticsearch
    es = Elasticsearch("http://localhost:9200")
    for index_name in collection_index:
        # 先删除已有索引
        if es.indices.exists(index=index_name):
            print("The index has already existed, going to remove it")
            es.options(ignore_status=404).indices.delete(index=index_name)
        if index_name == 'nvd':
            create_index_response = es.indices.create(index=index_name, body={
                "mappings": es_mappings.nvd_mappings
            })
            print(create_index_response)
        else:
            print("UNSUPPORTED INDEX NAME!!")
        # elif index_name == 'relation':
        #     create_index_response = es.indices.create(index=index_name, body={
        #         "mappings": es_mappings.relation_mappings
        #     })
        #     print(create_index_response)


def write_to_es():
    establish_es_index()
    transfer_to_es()


def search_by_cve_id(cve_id):
    cve_id = cve_id.upper()
    # 不是有效的cve-id
    if not validate_cve_id(cve_id):
        return {
            'code': 500,
            'message': 'cve格式不正确！',
            'data': None
        }
    index_name = 'nvd'
    body = {
        "query": {
            "term": {
                "No": cve_id
            }
        }
    }

    es = Elasticsearch("http://localhost:9200")
    try:
        result = es.search(index=index_name, body=body)
    except Exception as e:
        print("es搜索出现异常：{},{}".format(e, e.__traceback__))
    print("query data: ", result)
    hits = result["hits"]["hits"]
    return {
        'code': 200,
        'message': '成功',
        'data': hits[0]["_source"] if hits else None
    }

