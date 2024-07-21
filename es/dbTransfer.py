from pymongo import MongoClient
from elasticsearch import Elasticsearch
from queue import Queue
from threading import Thread
from es.es_util import establish_es_index

collection_to_index = {'mergedCVE': 'merged_cve'}
collection = 'mergedCVE'
index = 'merged_cve'

# 连接到MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['local']
db_collection = db[collection]  # 集合名称
# 连接到es
es = Elasticsearch("http://localhost:9200")

# 定义线程数和队列大小
NUM_THREADS = 4
QUEUE_SIZE = 1000

data_queue = Queue(QUEUE_SIZE)


def get_from_mongo(time=None):

    # 读取数据
    # 全量读取数据
    if time is None:
        db_data = list(db_collection.find({}))
    # 非全量读取数据
    else:
        query = {
            "$or": [
                {"cve_published_time": {"$gte": time}},
                {"cve_modified_time": {"$gte": time}}
            ]
        }
        db_data = list(db_collection.find(query))
    print(db_data)

    for doc in db_data:
        data_queue.put(doc)

    # 在队列末尾放特殊标记表示已经完成数据获取
    data_queue.put(None)


def write_to_es():
    _index = index
    while True:
        doc_with_id = data_queue.get() #从队列获取数据
        if doc_with_id is None:
            break # 遇到特殊标记，停止循环

        cve_id = doc_with_id['No']
        doc = {
            'No': cve_id,
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
        body = {
            "query": {
                "term": {"No": cve_id}
            }
        }
        # 查找是否存在该文档，如果存在则是更新，否则是插入
        result = es.search(index=_index, body=body)
        hits = result["hits"]["hits"]
        # 更新
        if hits:
            doc_id = result['hits']['hits'][0]['_id']
            response = es.update(index=_index, id=doc_id, body={"doc": doc})
        else:
            response = es.index(index=_index, document=doc)
        print(response['result'])


def transfer_to_es(time=None):
    threads = []

    # 如果没有索引创建已有索引
    if not es.indices.exists(index=index):
        print("没有对应的索引，正在创建")
        establish_es_index()
        print("创建索引完成")

    # 创建获取数据线程
    thread = Thread(target=get_from_mongo, args=(time,))
    threads.append(thread)
    thread.start()

    # 创建存入数据的线程
    for _ in range(NUM_THREADS):
        thread = Thread(target=write_to_es)
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

# if __name__ == "__main__":
#     for collection, index in collection_to_index.items():
#         mongo_data = get_from_mongo(collection)
#         write_to_es(index, mongo_data)
