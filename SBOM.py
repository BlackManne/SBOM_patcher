from fastapi import FastAPI
from spider.nvd_spider import *
from es.es_util import search_by_cve_id, establish_es_index, search_by_query
from es.dbTransfer import transfer_to_es
from mongoDB.mongoQuery import query_nvd_by_cve_id, query_aliyun_by_cve_id
from Utils.util import heartbeat
app = FastAPI()


@app.post('/nvd/crawl/all')
def nvd_crawl_all():
    crawl_all()
    # todo 添加阿里云爬虫的入口
    # todo 阿里云合并的入口
    establish_es_index()
    transfer_to_es()


@app.post('/nvd/crawl/by_time/{start_time}')
def nvd_crawl_by_time(start_time: str):
    # 格式为 2024-07-11
    crawl_by_time(start_time=start_time)


@app.get('/get/merged/{cve_id}')
def query_by_cve_id(cve_id: str):
    return search_by_cve_id(cve_id=cve_id)


@app.get('/get/merged/{query}')
def query_by_expression(query: str):
    return search_by_query(body=query)


@app.get('/get/nvd/{cve_id}')
def query_mongo_nvd_by_cve_id(cve_id: str):
    return query_nvd_by_cve_id(cve_id=cve_id)


@app.get('/get/aliyun/{cve_id}')
def query_mongo_aliyun_by_cve_id(cve_id: str):
    return query_aliyun_by_cve_id(cve_id=cve_id)


@app.get('/heartbeat')
def check_heartbeat():
    return {
        'code': 200,
        'message': '成功',
        'data': heartbeat()
    }
