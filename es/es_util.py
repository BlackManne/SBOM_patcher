# 用来创建es的两个index
from elasticsearch import Elasticsearch
import es_mappings

# collection_index = {'nvd', 'relation'}
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


if __name__ == "__main__":
    establish_es_index()
