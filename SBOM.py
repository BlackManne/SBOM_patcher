from fastapi import FastAPI
from spider.nvd_spider import *

app = FastAPI()


@app.post('/nvd/crawl/all')
def nvd_crawl_all():
    crawl_all()


@app.post('/nvd/crawl/by_time/start_time=<string:start_time>/end_time=<string:end_time>')
def nvd_crawl_by_time(start_time, end_time):
    crawl_by_time(start_time=start_time, end_time=end_time)


@app.get('/get/cve_id=<string:cve_id>')
def query_by_cve_id(cve_id):
    if len(cve_id.split('-')) != 3:
        print("CVE格式不正确！")

