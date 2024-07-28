import re

import requests
from random import randint

from elasticsearch import Elasticsearch
from urlextract import URLExtract
from Constants.dbConstants import es_url, mongo_url
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def github_url_transfer(url):
    # 把每一个github url转换为调用api.github.com的链接
    return str(url).replace("github.com", "api.github.com/repos")


def get_page_content(url, session=None):
    user_agent = [
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    try:
        if session is None:
            response = requests.get(url, headers={'User-Agent': user_agent[randint(0, 1)]})
        else:
            response = session.get(url, headers={'User-Agent': user_agent[randint(0, 1)]})
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return response.text
        return
    except Exception:
        return


def get_URL_from_text(text):
    urlExtractor = URLExtract()
    return list(set(urlExtractor.find_urls(text)))


def validate_cve_id(cve_id):
    pattern = r'^CVE-\d{4}-\d{4,}$'
    match = re.match(pattern, cve_id)
    if match:
        return True
    else:
        return False


def check_elasticsearch():
    es = Elasticsearch(es_url)
    return es.ping()


def check_mongodb():
    client = MongoClient(mongo_url)
    try:
        client.server_info()
        return True
    except ConnectionFailure:
        return False


def heartbeat():
    es_status = check_elasticsearch()
    mongo_status = check_mongodb()
    overall_status = all([es_status, mongo_status])
    return {
        'es_status': es_status,
        'mongo_status': mongo_status,
        'SBOM_status': True,
        'all_status': overall_status
    }
