from pymongo import MongoClient
from elasticsearch import Elasticsearch

collection_to_index = {'nvd': 'nvd'}


def get_from_mongo(_collection):
    # 连接到MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['local']
    db_collection = db[_collection]  # 集合名称
    # 读取数据
    db_data = list(db_collection.find({}))
    print(db_data)
    return db_data


def write_to_es(_index, _data):
    # 连接到Elasticsearch
    es = Elasticsearch("http://localhost:9200")

    # 先删除已有索引
    if not es.indices.exists(index=_index):
        print("no such index!!")
        return

    if _index == 'nvd':
        for doc_with_id in _data:
            doc = {
                'No': doc_with_id['No'],
                'title': doc_with_id['title'],
                'description': doc_with_id['description'],
                'score': doc_with_id['score'],
                'source_url': doc_with_id['source_url'],
                'affected_software': doc_with_id['affected_software'],
                'third_party_list': doc_with_id['third_party_list'] if doc_with_id['third_party_list'] is not None else None,
                'vendor_list': doc_with_id['vendor_list'] if doc_with_id['vendor_list'] is not None else None,
                'exploit_list': doc_with_id['exploit'] if doc_with_id['exploit'] is not None else None,
                'patch_list': doc_with_id['patch_list'] if doc_with_id['patch_list'] is not None else None,
            }
            response = es.index(index=_index, document=doc)
            print(response['result'])


def transfer_to_es():
    for collection, index in collection_to_index.items():
        mongo_data = get_from_mongo(collection)
        write_to_es(index, mongo_data)


# if __name__ == "__main__":
#     for collection, index in collection_to_index.items():
#         mongo_data = get_from_mongo(collection)
#         write_to_es(index, mongo_data)
