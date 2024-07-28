from elasticsearch import Elasticsearch
from Constants.dbConstants import es_url
es = Elasticsearch(es_url)

index_name = 'openeuler-22.03-lts-sp3'


def check_rpm_exists(rpm_name):
    # 查询 DSL
    # es 默认会忽略大小写，但确保索引时 rpm_name 字段是 text 类型且使用了标准分析器。
    query = {
        "query": {
            "wildcard": {
                "rpm_name.keyword": f"*{rpm_name}*"
            }
        }
    }

    response = es.search(index=index_name, body=query)

    # 如果包存在于索引中
    if response['hits']['total']['value'] > 0:
        return True
    else:
        return False


rpm_name_to_check = "CUnit"
exists = check_rpm_exists(rpm_name_to_check)

if exists:
    print(f"RPM 包 '{rpm_name_to_check}' 存在于索引 '{index_name}' 中。")
else:
    print(f"RPM 包 '{rpm_name_to_check}' 不存在于索引 '{index_name}' 中。")
