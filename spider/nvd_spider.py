import math
import queue
import threading
from threading import Thread
from datetime import datetime, timedelta, date

import requests
from bs4 import BeautifulSoup

from ExternalSearchers.nvd_searcher import search_nvd_using_cve_id, headers
from Constants.dbConstants import client

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


mongodb_client = client
db = mongodb_client['local']
nvd_collection = db['nvd']


def write_to_mongo():
    while True:
        data = data_queue.get()
        if data is None:
            break
        # 将数据写入 MongoDB
        cve_id = data['No']

        # 构建查询条件
        query = {'No': cve_id}
        # 查询是否存在该cve-id，若有则为更新
        existing_document = nvd_collection.find_one(query)

        # 已经存在文档的话则更新
        if existing_document:
            nvd_collection.update_one(query, {"$set": data})
        else:
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
    print(f"找到符合条件的结果{nvd_total_num}条")
    if nvd_total_num == 0:
        return
    pages = math.ceil(nvd_total_num / 20)
    print(f"共有{pages}页")

    producer_threads = [Thread(target=crawl_nvd_page, args=(base_url, i, pages)) for i in range(0, thread_num)]

    consumer_thread = threading.Thread(target=write_to_mongo)

    for thread in producer_threads:
        thread.start()

    consumer_thread.start()

    for thread in producer_threads:
        thread.join()  # 等待所有爬取线程完成

    data_queue.put(None)

    consumer_thread.join()  # 等待写入mongo线程完成

    mongodb_client.close()


def nvd_crawl_by_time(start_time):
    # 获取当前日期
    today = date.today()
    # 将日期转换为所需格式
    end_time = today.strftime("%Y-%m-%d")
    print(end_time)
    start_datetime = datetime.strptime(start_time, "%Y-%m-%d")
    end_datetime = datetime.strptime(end_time, "%Y-%m-%d")
    # 计算两个日期之间的时间差
    delta = end_datetime - start_datetime
    # 检查时间差是否等于120天
    is_within_120_days = delta <= timedelta(days=120)
    if not is_within_120_days:
        print(f'开始时间和结束时间差值不能超过120天，输入的差值为:{delta}')
        return
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
    base_url = f'https://nvd.nist.gov/vuln/search/results?form_type=Advanced&results_type=overview&search_type=all&isCpeNameSearch=false&pub_start_date={start_month}%2F{start_day}%2F{start_year}&pub_end_date={end_month}%2F{end_day}%2F{end_year}&mod_start_date={start_month}%2F{start_day}%2F{start_year}&mod_end_date={end_month}%2F{end_day}%2F{end_year}&startIndex='
    crawl_nvd(base_url)


def nvd_crawl_all():
    base_url = "https://nvd.nist.gov/vuln/search/results?isCpeNameSearch=false&results_type=overview&form_type=Basic&search_type=all&startIndex="
    crawl_nvd(base_url)


if __name__ == "__main__":
    nvd_crawl_by_time("2024-06-11")