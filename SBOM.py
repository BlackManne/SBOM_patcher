import json

from spider.AliCloud_spider import *
from spider.nvd_spider import *
from es.es_util import search_by_cve_id, establish_es_index, search_by_query
from es.dbTransfer import transfer_to_es, transfer_by_cve_list
from mongoDB.mongoUtils import query_by_cve_id_and_db_name
from mongoDB.mergeCollections import merge_mongo_database, merge_mongo_by_cve_list
from Utils.util import heartbeat
from flask import Flask, request, jsonify
app = Flask(__name__)


@app.route('/nvd/crawl/all', methods=['POST'])
def crawl_all():
    nvd_crawl_all()
    alicloud_crawl_all()
    merge_mongo_database()
    establish_es_index()
    transfer_to_es()
    return jsonify({"message": "获取成功"}), 200


@app.route('/nvd/crawl/by_start_time', methods=['POST'])
def crawl_by_start_time():
    start_time = request.args.get('start_time')
    # 格式为 2024-07-11
    nvd_crawl_by_time(start_time=start_time)
    alicloud_crawl_by_time(start_time=start_time)
    merge_mongo_database(start_time=start_time)
    establish_es_index()
    transfer_to_es(start_time=start_time)
    return jsonify({"message": "获取成功"}), 200


@app.route('/nvd/crawl/by_time', methods=['POST'])
def crawl_by_time():
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    # 格式为 2024-07-11
    nvd_crawl_by_time(start_time=start_time, end_time=end_time)
    alicloud_crawl_by_time(start_time=start_time, end_time=end_time)
    merge_mongo_database(start_time=start_time, end_time=end_time)
    establish_es_index()
    transfer_to_es(start_time=start_time, end_time=end_time)
    return jsonify({"message": "获取成功"}), 200


@app.route('/crawl/by_cve_list', methods=['POST'])
def crawl_by_cve_list():
    cve_list_str = request.form.get('cve_list')
    cve_list = cve_list_str.split(',')
    crawl_nvd_by_cve_list(cve_list)
    # crawl_aliyun_by_cve_list(cve_list)
    merge_mongo_by_cve_list(cve_list)
    establish_es_index()
    transfer_by_cve_list(cve_list)
    return jsonify({"message": "获取成功"}), 200


@app.route('/get_by_cve', methods=['GET'])
def query_es_by_cve_id():
    cve_id = request.args.get('cve_id')
    if not cve_id:
        return jsonify({"message": "没有找到cve_id参数！"}), 400
    data = search_by_cve_id(cve_id=cve_id)
    return jsonify({
        'message': data['message'],
        'data': data['data']
    }), data['code']


@app.route('/get_by_query', methods=['GET'])
def query_es_by_expression():
    query = request.args.get('query')
    # 去掉多余的字符
    # 使用正则表达式删除所有空白字符
    query = re.sub(r'\s+', '', query)
    query = json.loads(query)
    if not query:
        return jsonify({"message": "没有找到query参数！"}), 400
    data = search_by_query(body=query)
    return jsonify({
        'message': data['message'],
        'data': data['data']
    }), data['code']


@app.route('/get_by_db_cve', methods=['GET'])
def query_mongo_by_cve_id_and_db_name():
    cve_id = request.args.get('cve_id')
    db_name = request.args.get('db_name')
    if not cve_id:
        return jsonify({"message": "没有找到cve_id参数！"}), 400
    if not db_name:
        return jsonify({"message": "没有找到db_name参数！"}), 400
    data = query_by_cve_id_and_db_name(cve_id=cve_id, db_name=db_name)
    return jsonify({
        'message': data['message'],
        'data': data['data']
    }), data['code']


@app.route('/heartbeat',methods=['GET'])
def check_heartbeat():
    return jsonify({
        'message': '成功',
        'data': heartbeat()
    }), 200


@app.route('/', methods=['GET'])
def hello():
    return jsonify({"message": "欢迎来到SBOM_patcher漏洞爬取系统！"}), 200


# @app.route('/manual_merge', methods=['POST'])
# def manual_merge_by_time():
#     start_time = request.args.get('start_time')
#     end_time = request.args.get('end_time')
#     # 格式为 2024-07-11
#     merge_mongo_database_manual(start_time=start_time,end_time=end_time)
#     establish_es_index()
#     transfer_to_es(start_time=start_time, end_time=end_time)
#     return jsonify({"message": "获取成功"}), 200


if __name__ == "__main__":
    app.run()


