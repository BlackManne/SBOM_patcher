import requests
from pymongo import MongoClient

from Constants.dbConstants import mongo_url
from ExternalSearchers.debian_searcher import debian_search_by_cve_id
from ExternalSearchers.github_searcher import advisories_search_by_id
from ExternalSearchers.nvd_searcher import search_nvd_using_cve_id
from Utils.util import get_page_content
from mongoDB.mergeCollections import merge_mongo_by_nvd_docs
from spider.AliCloud_spider import crawl_one_by_cve_id

headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Connection': 'keep-alive'
}

if __name__ == "__main__":
    print(get_page_content("https://avd.aliyun.com/nvd/list?type=WEB应用&page="))
    # cve_id = "CVE-2023-50868"
    # nvd_detail = search_nvd_using_cve_id(cve_id)
    # print(nvd_detail)
    # crawl_one_by_cve_id(cve_id)
    # debian_detail = debian_search_by_cve_id(cve_id)
    # print(debian_detail)
    # advisories_detail = advisories_search_by_id(cve_id)
    # print(advisories_detail)
    # 连接MongoDB
    # mongodb_client = MongoClient(mongo_url)
    # db = mongodb_client['local']
    # nvd_new_collection = db['nvd']
    # nvd_new_collection.insert_one(nvd_detail)
    # nvd_docs = nvd_new_collection.find_one({'No': cve_id})
    # merge_mongo_by_nvd_docs([nvd_docs])
