from elasticsearch import Elasticsearch
from pymongo import MongoClient

es_url = "http://localhost:9200"
mongo_url = "mongodb://localhost:27017"
# es_url = 'http://elasticsearch:9200'
# mongo_url = "mongodb://mongodb:27017/"

es_username = 'elastic'
es_password = '123456'


def create_es_connection():
    return Elasticsearch([es_url], http_auth=(es_username, es_password))


def create_mongo_connection():
    return MongoClient(mongo_url)



