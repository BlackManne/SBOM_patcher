import unittest

from datetime import datetime, timedelta
from mongoDB.mongoUtils import query_by_updated_time, query_by_cve_id_and_db_name
from Tests.Utils.test_utils import save_html, save_json, get_html_from_url
import time

import SBOM

db_name_collections_by_time = {'nvd', 'aliCloud', 'mergedCVE'}
db_name_collections_by_number = {'debian', 'githubAdvisories'}


class TestSBOMSpider(unittest.TestCase):

    def test_SBOM_crawl_by_time(self):
        # 获取当前日期
        current_date = datetime.now()
        # 计算昨天的日期
        yesterday = current_date - timedelta(days=1)

        # 格式化昨天的日期为字符串
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        print(yesterday_str)

        exec_start_time = time.time()

        SBOM.nvd_crawl_by_time(start_time=yesterday_str)
        SBOM.alicloud_crawl_by_time(start_time=yesterday_str)
        SBOM.merge_mongo_database(time=yesterday_str)
        SBOM.establish_es_index()
        SBOM.transfer_to_es(time=yesterday_str)

        exec_end_time = time.time()

        execution_time = exec_end_time - exec_start_time
        print(f"增量爬取一天内的数据的执行时间：{execution_time} 秒")

    def test_generate_testcases_of_yesterday(self):
        generate_testcases_of_yesterday()

    if __name__ == '__main__':
        unittest.main()


def generate_testcases_of_yesterday():
    # 生成testcases
    # 获取当前日期
    current_date = datetime.now()
    # 计算昨天的日期
    yesterday = current_date - timedelta(days=1)

    # 格式化昨天的日期为字符串
    yesterday_str = yesterday.strftime('%Y-%m-%d')

    for db_name in db_name_collections_by_time:
        generate_testcases_by_db(db_name, yesterday_str)
    nvd_docs = query_by_updated_time(yesterday_str, 'nvd')
    cve_id_list = [doc['No'] for doc in nvd_docs]
    for db_name in db_name_collections_by_number:
        generate_testcases_by_cve_id_list(db_name, cve_id_list)


def generate_testcases_by_cve_id_list(db_name, cve_id_list):
    for cve_id in cve_id_list:
        res = query_by_cve_id_and_db_name(cve_id=cve_id, db_name=db_name)
        if res['data'] is None:
            continue
        data = res['data']
        cve_id = data['No']
        filename = f'{db_name}_testcases_{cve_id}'
        url = data['source_url']
        raw_html = get_html_from_url(url)
        save_html(f'{filename}.html', raw_html.data)
        if '_id' in data:
            del data['_id']
        save_json(f'{filename}.json', data)


def generate_testcases_by_db(db_name, start_time):
    data_list = query_by_updated_time(start_time, db_name)
    for data in data_list:
        cve_id = data['No']
        filename = f'{db_name}_testcases_{cve_id}'
        # 合并后的数据库不需要爬取html
        if db_name != 'mergedCVE':
            url = data['source_url']
            raw_html = get_html_from_url(url)
            save_html(f'{filename}.html', raw_html.data)
        if '_id' in data:
            del data['_id']
        save_json(f'{filename}.json', data)

