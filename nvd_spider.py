import pymongo
from datetime import datetime
from ExternalSearchers.nvd_searcher import search_nvd

mongodb_client = pymongo.MongoClient("mongodb://localhost:27017")
# 选择local数据库和CVE集合
db = mongodb_client['local']
collection = db['CVE']
nvd_collection = db['NVD']

# todo 入库的逻辑修改为es，不用mongo了。注意在存储数据的时候，要把时间存进去，怎么获取系统时间下面有例子
# 查询集合中所有文档的No字段
for document in collection.find({}, {'No': 1, '_id': 0}):
    cve_id=document['No']
    print(cve_id)
    res = search_nvd(cve_id)
    nvd_collection.insert_one({'No': cve_id, 'info': res})
# # res = search_nvd('CVE-2023-23946')
# # nvd_collection.insert_one({'No': 'CVE-2023-23946', 'info': res})

# todo 获取系统时间的例子，别的方法也可
# 获取当前系统时间
now = datetime.now()
# 格式化为字符串
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
print(formatted_time)