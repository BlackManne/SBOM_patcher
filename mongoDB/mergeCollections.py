import datetime

from Constants.dbConstants import create_mongo_connection
from mongoDB.mongoUtils import query_by_updated_time, query_by_time_range, query_by_cve_id
from ExternalSearchers.debian_searcher import get_from_debian_by_cve_list
from ExternalSearchers.github_searcher import get_from_advisories_by_cve_list
from mongoDB.mongoUtils import insert_or_update_by_cve_id

# 连接MongoDB
mongodb_client = create_mongo_connection()
db = mongodb_client['local']

# 获取集合
nvd_db_name = 'nvd'
merged_cve_db_name = 'mergedCVE'
nvd_new_collection = db['nvd']
alicloud_collection = db['aliCloud']
merged_cve_collection = db['mergedCVE']


def merge_mongo_database(start_time=None, end_time=None):
    # 此时是全量查询
    if start_time is None:
        # 全量查询需要将合并后的mongo表先清空
        merged_cve_collection.delete_many({})
        nvd_docs = nvd_new_collection.find({})
    elif end_time is None:
        nvd_docs = query_by_updated_time(start_time, nvd_db_name)
    else:
        nvd_docs = query_by_time_range(start_time=start_time, end_time=end_time, db_name=nvd_db_name)
    merge_mongo_by_nvd_docs(nvd_docs)


def merge_mongo_by_cve_list(cve_list):
    nvd_docs = []
    for cve_id in cve_list:
        result = query_by_cve_id(nvd_new_collection, cve_id)['data']
        if result is None:
            continue
        nvd_docs.append(result)
    merge_mongo_by_nvd_docs(nvd_docs)


def merge_mongo_database_manual(start_time=None, end_time=None):
    if end_time is None:
        nvd_docs = query_by_updated_time(start_time, nvd_db_name)
    else:
        nvd_docs = query_by_time_range(start_time=start_time, end_time=end_time, db_name=nvd_db_name)
    merge_mongo_by_nvd_docs_manual(nvd_docs)


def merge_mongo_by_nvd_docs(nvd_docs):
    if nvd_docs is None:
        print('发生错误！传入参数为None')
        return
    # 获取nvd列表里面全部的cve_id
    cve_id_list = [doc['No'] for doc in nvd_docs]
    # 根据nvd增量或者全量爬取debian和advisories
    debian_list = get_from_debian_by_cve_list(cve_id_list)
    advisories_list = get_from_advisories_by_cve_list(cve_id_list)
    # 根据nvd的增量将aliyun、advisory和debian都合并
    for nvd_doc in nvd_docs:
        cve_id = nvd_doc['No']
        cve_no = cve_id[3:]

        # 在AliCloud表中查找对应的漏洞信息
        alicloud_doc = alicloud_collection.find_one({'No': 'AVD' + cve_no})
        if not alicloud_doc:
            alicloud_doc = alicloud_collection.find_one({'No': 'CVE' + cve_no})

        merged_doc = {
            'No': nvd_doc.get('No'),
            'title': nvd_doc.get('title'),
            'cve_published_time': nvd_doc.get('cve_published_time'),
            'cve_modified_time': nvd_doc.get('cve_modified_time'),
            'merge_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'description': {
                'nvd_description': nvd_doc.get('description')
            },
            'score': nvd_doc.get('score'),
            'source_urls': {
                'nvd_source_url': nvd_doc.get('source_url')
            },
            'affected_software': nvd_doc.get('affected_software'),
            'third_party_list': nvd_doc.get('third_party_list'),
            'vendor_list': nvd_doc.get('vendor_list'),
            'exploit': nvd_doc.get('exploit'),
            'patch_list': {
                'nvd': nvd_doc.get('patch_list')
            }
        }
        # 如果在AliCloud中找到了对应的记录，则合并数据
        if alicloud_doc:
            merged_doc['name'] = alicloud_doc.get('name')
            merged_doc['type'] = alicloud_doc.get('type')
            merged_doc['description']['alicloud_description'] = alicloud_doc.get('description')
            merged_doc['rate'] = alicloud_doc.get('rate')
            merged_doc['source_urls']['alicloud_source_url'] = alicloud_doc.get('source_url')
            merged_doc['affected_software'] += alicloud_doc.get('affected_software')
            merged_doc['alicloud_list'] = alicloud_doc.get('reference')
        # 如果有debian数据，合并
        if debian_list is not None and cve_id in debian_list:
            debian_data = debian_list[cve_id]
            merged_doc['debian_list'] = debian_data['ref_links']
            merged_doc['debian_patch_reference'] = debian_data['patch_reference']
            merged_doc['source_urls']['debian'] = debian_data['source_url']
            if debian_data['patch_list'] is not None:
                merged_doc['patch_list']['debian'] = debian_data['patch_list']
        # 如果有advisory数据，合并
        if advisories_list is not None and cve_id in advisories_list:
            advisories_data = advisories_list[cve_id]
            merged_doc['advisories_list'] = advisories_data['reference']
            merged_doc['source_urls']['advisories'] = advisories_data['source_url']
            merged_doc['github_advisories_patches'] = advisories_data['patches']

        # 插入或更新MergedCVE表
        cve_id = nvd_doc.get('No')
        insert_or_update_by_cve_id(cve_id=cve_id, doc=merged_doc, collection_name=merged_cve_db_name)

        print(f"编号为{cve_id}的数据合并完成。")


def merge_mongo_by_nvd_docs_manual(nvd_docs):
    if nvd_docs is None:
        print('发生错误！传入参数为None')
        return
    # 根据nvd的增量将aliyun、advisory和debian都合并
    for nvd_doc in nvd_docs:
        cve_id = nvd_doc['No']
        cve_no = cve_id[3:]

        # 在AliCloud表中查找对应的漏洞信息
        alicloud_doc = alicloud_collection.find_one({'No': 'AVD' + cve_no})
        if not alicloud_doc:
            alicloud_doc = alicloud_collection.find_one({'No': 'CVE' + cve_no})

        merged_doc = {
            'No': nvd_doc.get('No'),
            'title': nvd_doc.get('title'),
            'cve_published_time': nvd_doc.get('cve_published_time'),
            'cve_modified_time': nvd_doc.get('cve_modified_time'),
            'merge_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'description': {
                'nvd_description': nvd_doc.get('description')
            },
            'score': nvd_doc.get('score'),
            'source_urls': {
                'nvd_source_url': nvd_doc.get('source_url')
            },
            'affected_software': nvd_doc.get('affected_software'),
            'third_party_list': nvd_doc.get('third_party_list'),
            'vendor_list': nvd_doc.get('vendor_list'),
            'exploit': nvd_doc.get('exploit'),
            'patch_list': {
                'nvd': nvd_doc.get('patch_list')
            }
        }
        # 如果在AliCloud中找到了对应的记录，则合并数据
        if alicloud_doc:
            merged_doc['name'] = alicloud_doc.get('name')
            merged_doc['type'] = alicloud_doc.get('type')
            merged_doc['description']['alicloud_description'] = alicloud_doc.get('description')
            merged_doc['rate'] = alicloud_doc.get('rate')
            merged_doc['source_urls']['alicloud_source_url'] = alicloud_doc.get('source_url')
            merged_doc['affected_software'] += alicloud_doc.get('affected_software')
            merged_doc['alicloud_list'] = alicloud_doc.get('reference')
        # 如果有debian数据，合并
        debian_data = query_by_cve_id(db['debian'], cve_id)['data']
        if debian_data is None:
            debian_datas = get_from_debian_by_cve_list([cve_id])
            if cve_id in debian_datas:
                debian_data = debian_datas[cve_id]
                merged_doc['debian_list'] = debian_data['ref_links']
                merged_doc['debian_patch_reference'] = debian_data['patch_reference']
                merged_doc['source_urls']['debian'] = debian_data['source_url']
                if debian_data['patch_list'] is not None:
                    merged_doc['patch_list']['debian'] = debian_data['patch_list']
        # 如果有advisory数据，合并
        advisories_data = query_by_cve_id(db['githubAdvisories'], cve_id)['data']
        if advisories_data is None:
            advisories_datas = get_from_advisories_by_cve_list([cve_id])
            if cve_id in advisories_datas:
                advisories_data = advisories_datas[cve_id]
                merged_doc['advisories_list'] = advisories_data['reference']
                merged_doc['source_urls']['advisories'] = advisories_data['source_url']
                merged_doc['github_advisories_patches'] = advisories_data['patches']

        # 插入或更新MergedCVE表
        cve_id = nvd_doc.get('No')
        insert_or_update_by_cve_id(cve_id=cve_id, doc=merged_doc, collection_name=merged_cve_db_name)

        print(f"编号为{cve_id}的数据合并完成。")