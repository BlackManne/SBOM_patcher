import logging
import re

import pymongo
import requests
from random import randint

from urlextract import URLExtract
from Constants.dbConstants import create_es_connection, create_mongo_connection
from pymongo.errors import ConnectionFailure

from RefPageParsers.github_parser import github_parse

cve_pattern = r'^CVE-\d{4}-\d{4,}$'

es = create_es_connection()
client = create_mongo_connection()


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


def parse_patch_url(url):
    # 首先初始化为不能解析的数据
    patch_detail = {
        'detail': None,
        'service_name': 'others'
    }
    # 根据传入的patch url解析，调用不同的parse函数
    if re.match("https://github.com/.+", url):
        github_detail = github_parse(url)
        patch_detail['detail'] = github_detail['detail']
        patch_detail['service_name'] = github_detail['service_name']
    elif re.match("https://msrc.microsoft.com/.+", url):
        patch_detail['service_name'] = 'microsoft'
    elif re.match("https://osv.dev/vulnerability/.+", url):
        patch_detail['service_name'] = 'osv_dev'
    elif re.match(r"https://bugzilla.redhat.com/show_bug.cgi?id=" + cve_pattern, url):
        patch_detail['service_name'] = 'redhat'
    elif re.match(r"https://ubuntu.com/security/" + cve_pattern, url):
        patch_detail['service_name'] = 'ubuntu'
    elif re.match(r"https://security-tracker.debian.org/tracker/" + cve_pattern, url):
        patch_detail['service_name'] = 'debian'
    return patch_detail


def validate_cve_id(cve_id):
    match = re.match(cve_pattern, cve_id)
    if match:
        return True
    else:
        return False


def check_elasticsearch():
    try:
        res = es.ping()
        return res
    except Exception as e:
        logging.info("ping es出现异常：{},{}".format(e, e.__traceback__))
        return False


def check_mongodb():
    try:
        client.server_info()
        return True
    except pymongo.errors.ServerSelectionTimeoutError as e:
        logging.info("ping mongo出现异常：{},{}".format(e, e.__traceback__))
    except Exception as e:
        print("An error occurred:", e)


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
