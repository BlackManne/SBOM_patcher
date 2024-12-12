from Constants.dbConstants import create_mongo_connection

# 连接MongoDB
mongodb_client = create_mongo_connection()
db = mongodb_client['local']

db_name_collections = {'nvd', 'aliCloud', 'debian', 'githubAdvisories', 'mergedCVE'}


def query_by_cve_id(collection, cve_id):
    try:
        result = collection.find_one({'No': cve_id})
        if result is None:
            return {
                'code': 200,
                'message': "不存在该编号的cve！",
                "data": result
            }
        if result['_id'] is not None:
            del result['_id']
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
    if db_name not in db_name_collections:
        print('数据库名称错误')
        return None
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


def query_by_time_range(start_time, end_time, db_name):
    if db_name not in db_name_collections:
        print('数据库名称错误')
        return None
    db_collection = db[db_name]
    if start_time is None or end_time is None:
        print(f"参数不对！起始时间为{start_time}，结束时间为{end_time}，均不能为空")
        return
    # 非全量读取数据
    else:
        query = {
            "$or": [
                {"cve_published_time": {"$gte": start_time, "$lte": end_time}},
                {"cve_modified_time": {"$gte": start_time, "$lte": end_time}}
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
