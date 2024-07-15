import math
import queue
import threading
from threading import Thread

import pymongo
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pymongo import collection

from ExternalSearchers.nvd_searcher import search_nvd_using_cve_id, headers


def transfer_mongo_to_es():
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
        res = search_nvd_using_cve_id(cve_id)
        nvd_collection.insert_one({'No': cve_id, 'info': res})
    # # res = search_nvd('CVE-2023-23946')
    # # nvd_collection.insert_one({'No': 'CVE-2023-23946', 'info': res})


    # 获取当前系统时间
    now = datetime.now()
    # 格式化为字符串
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(formatted_time)


thread_num = 5
data_queue = queue.Queue()


def crawl_nvd_page(base_url, nowpage, maxpages):
    while nowpage <= maxpages:
        url = base_url + str(nowpage * 20)
        response = requests.request("GET", url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        cve_ids = soup.select('[data-testid^="vuln-detail-link-"]')
        for e in cve_ids:
            cve_id = e.text
            result = search_nvd_using_cve_id(cve_id)
            data_queue.put(result)
            print(result)
        nowpage += thread_num


mongodb_client = pymongo.MongoClient("mongodb://localhost:27017")
db = mongodb_client['local']
nvd_collection = db['NVD_NEW']


def write_to_mongo():
    while True:
        data = data_queue.get()
        # 将数据写入 MongoDB
        nvd_collection.insert_one(data)
        data_queue.task_done()


def crawl_nvd(base_url):
    response = requests.request("GET", base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    element = soup.find(attrs={'data-testid': 'vuln-matching-records-count'})
    if element is None:
        print("error!!!cannot get nvd page!!!")
        return
    # 获取元素的内容
    nvd_total_num = int(element.text.replace(',', ''))
    pages = math.ceil(nvd_total_num / 20)

    mongodb_thread = threading.Thread(target=write_to_mongo)
    mongodb_thread.start()

    threads = [Thread(target=crawl_nvd_page, args=(base_url, i, pages)) for i in range(0, thread_num)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()  # 等待所有线程完成

    data_queue.join()

    mongodb_thread.join()

    mongodb_client.close()


def crawl_by_time():
    input_string = input("请输入开始时间和结束时间，格式均为yyyy-mm-dd，用空格隔开，例如:2024-07-11 2024-07-12:\n")
    if input_string is None:
        print("您尚未输入任何字符串！")
        return
    if len(input_string.split(' ')) != 2:
        print("输入格式不对")
        return
    input_arrays = input_string.split(' ')
    start_time = input_arrays[0]
    end_time = input_arrays[1]
    start_arrays = str(start_time).split('-')
    end_arrays = str(end_time).split('-')
    if len(end_arrays) != 3 or len(start_arrays) != 3:
        print('输入的日期格式不对！！格式应该如:2024-07-11')
        return
    start_year = start_arrays[0]
    start_month = start_arrays[1]
    start_day = start_arrays[2]
    end_year = end_arrays[0]
    end_month = end_arrays[1]
    end_day = end_arrays[2]
    base_url = f'https://nvd.nist.gov/vuln/search/results?form_type=Advanced&results_type=overview&search_type=all&isCpeNameSearch=false&pub_start_date={start_month}%2F{start_day}%2F{start_year}&pub_end_date={end_month}%2F{end_day}%2F{end_year}&mod_start_date={start_month}%2F{start_day}%2F2024&{start_year}&mod_end_date={end_month}%2F{end_day}%2F{end_year}&startIndex='
    crawl_nvd(base_url)


def crawl_all():
    base_url = "https://nvd.nist.gov/vuln/search/results?isCpeNameSearch=false&results_type=overview&form_type=Basic&search_type=all&startIndex="
    crawl_nvd(base_url)


if __name__ == "__main__":
    crawl_all()