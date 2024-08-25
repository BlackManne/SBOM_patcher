from fastapi import FastAPI

from spider.AliCloud_spider import *
from spider.nvd_spider import *
from es.es_util import search_by_cve_id, establish_es_index, search_by_query
from es.dbTransfer import transfer_to_es
from mongoDB.mongoUtils import query_by_cve_id_and_db_name
from mongoDB.mergeCollections import merge_mongo_database
from Utils.util import heartbeat
app = FastAPI()


@app.post('/nvd/crawl/all')
def crawl_all():
    nvd_crawl_all()
    alicloud_crawl_all()
    merge_mongo_database()
    establish_es_index()
    transfer_to_es()


@app.post('/nvd/crawl/by_time/{start_time}')
def crawl_by_time(start_time: str):
    # 格式为 2024-07-11
    nvd_crawl_by_time(start_time=start_time)
    alicloud_crawl_by_time(start_time=start_time)
    merge_mongo_database(time=start_time)
    establish_es_index()
    transfer_to_es(time=start_time)


@app.get('/get/merged/{cve_id}')
def query_es_by_cve_id(cve_id: str):
    return search_by_cve_id(cve_id=cve_id)


@app.get('/get/merged/{query}')
def query_es_by_expression(query: str):
    return search_by_query(body=query)


@app.get('/get/{db_name}}/{cve_id}')
def query_mongo_by_cve_id_and_db_name(db_name: str, cve_id: str):
    return query_by_cve_id_and_db_name(cve_id=cve_id, db_name=db_name)


@app.get('/heartbeat')
def check_heartbeat():
    return {
        'code': 200,
        'message': '成功',
        'data': heartbeat()
    }

