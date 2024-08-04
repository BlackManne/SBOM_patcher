from pymongo import MongoClient
from Constants.dbConstants import mongo_url

# 连接MongoDB
mongodb_client = MongoClient(mongo_url)
db = mongodb_client['local']

db_name_collections = {'nvd', 'aliCloud', 'debian', 'githubAdvisories', 'mergedCVE'}


def query_by_cve_id(collection, cve_id):
    try:
        result = collection.find_one({'No': cve_id})
        return {
            'code': 200,
            'message': "成功",
            "data": result
        }
    except Exception as e:
        print("mongo搜索出现异常：{},{}".format(e, e.__traceback__))
        return {
            'code': 500,
            'message': "查询服务端错误",
            "data": None
        }


def query_by_updated_time(time, db_name):
    db_collection = db[db_name]
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
    return db_data


def query_by_cve_id_and_db_name(cve_id, db_name):
    if db_name not in db_name_collections:
        print(f'不存在名为{db_name}的数据库！')
        return {
            'code': 500,
            'message': "不存在该数据库！！请检查数据库名称是否正确",
            "data": None
        }
    collection = db[db_name]
    return query_by_cve_id(collection=collection, cve_id=cve_id)


def insert_or_update_by_cve_id(cve_id, doc, collection_name):
    collection = db[collection_name]
    query = {'No': cve_id}
    collection.update_one(query, {'$set': doc}, upsert=True)
