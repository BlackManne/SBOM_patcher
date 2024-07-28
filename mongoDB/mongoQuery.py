from pymongo import MongoClient
from Constants.dbConstants import mongo_url

# 连接MongoDB
mongodb_client = MongoClient(mongo_url)
db = mongodb_client['local']


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


def query_nvd_by_cve_id(cve_id):
    nvd_collection = db['nvd']
    return query_by_cve_id(nvd_collection, cve_id)


def query_aliyun_by_cve_id(cve_id):
    aliyun_collection = db['aliCloud']
    return query_by_cve_id(aliyun_collection, cve_id)
