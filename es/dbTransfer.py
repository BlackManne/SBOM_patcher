from pymongo import MongoClient
from elasticsearch import Elasticsearch

collection_to_index = {'NVD': 'nvd', 'relation': 'relation'}


def get_from_mongo(_collection):
    # 连接到MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['local']
    db_collection = db[_collection]  # 集合名称
    # 读取数据
    db_data = list(db_collection.find({}).limit(10))
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
            info = doc_with_id['info']
            doc = {
                'No': doc_with_id['No'],
                'title': info['title'],
                'description': info['description'],
                'score': info['score'],
                'third_party_list': info['third_party_list'] if info['third_party_list'] is not None else None,
                'vendor_list': info['vendor_list'] if info['vendor_list'] is not None else None,
                'exploit_list': info['exploit'] if info['exploit'] is not None else None,
                'patch_list': info['patch_list'] if info['patch_list'] is not None else None,
                'patch_detail': info['patch_detail'] if info['patch_detail'] is not None else None,
            }
            response = es.index(index=_index, document=doc)
            print(response['result'])

    elif _index == 'relation':
        for doc_with_id in _data:
            doc = {
                'software': doc_with_id['software'],
                'related_cve': [{'cve_number': item['cve_number']} for item in doc_with_id['related_cve']]
            }
            response = es.index(index=_index, document=doc)
            print(response['result'])


if __name__ == "__main__":
    for collection, index in collection_to_index.items():
        mongo_data = get_from_mongo(collection)
        write_to_es(index, mongo_data)
