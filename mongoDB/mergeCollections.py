import datetime

from pymongo import MongoClient
from Constants.dbConstants import mongo_url
# 连接MongoDB
mongodb_client = MongoClient(mongo_url)
db = mongodb_client['local']

# 获取集合
nvd_new_collection = db['nvd']
alicloud_collection = db['aliCloud']
merged_cve_collection = db['mergedCVE']

# 清空MergedCVE表以避免重复插入
merged_cve_collection.delete_many({})

# 遍历NVD_NEW表中的所有数据
for nvd_doc in nvd_new_collection.find():
    cve_no = nvd_doc['No'][3:]

    # 在AliCloud表中查找对应的漏洞信息
    alicloud_doc = alicloud_collection.find_one({'No': 'AVD' + cve_no})
    if not alicloud_doc:
        alicloud_doc = alicloud_collection.find_one({'No': 'CVE' + cve_no})

    # 如果在AliCloud中找到了对应的记录，则合并数据
    if alicloud_doc:
        merged_doc = {
            'No': nvd_doc.get('No'),
            'title': nvd_doc.get('title'),
            'name': alicloud_doc.get('name'),
            'type': alicloud_doc.get('type'),
            'cve_published_time': nvd_doc.get('cve_published_time'),
            'cve_modified_time': nvd_doc.get('cve_modified_time'),
            'merge_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'description': {
                'nvd_description': nvd_doc.get('description'),
                'alicloud_description': alicloud_doc.get('description')
            },
            'score': nvd_doc.get('score'),
            'rate': alicloud_doc.get('rate'),
            'source_urls': {
                'nvd_source_url': nvd_doc.get('source_url'),
                'alicloud_source_url': alicloud_doc.get('source_url')
            },
            'affected_software': nvd_doc.get('affected_software') + alicloud_doc.get('affected_software'),
            'third_party_list': nvd_doc.get('third_party_list'),
            'vendor_list': nvd_doc.get('vendor_list'),
            'exploit': nvd_doc.get('exploit'),
            'patch_list': {
                'nvd': nvd_doc.get('patch_list'),
                'alicloud': alicloud_doc.get('patch_list')
            }
        }
    # 如果在AliCloud中未找到对应的记录，则保留原样
    else:
        merged_doc = nvd_doc

    # 插入或更新MergedCVE表
    merged_cve_collection.insert_one(merged_doc)

print("数据合并完成。")
