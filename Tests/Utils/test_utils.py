import json
import os

import requests

from Tests.Utils import HtmlResponse


def get_html_from_url(url):
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Connection': 'keep-alive'
    }
    try:
        response = requests.request("GET", url, headers=headers)
        if response.status_code != 200:
            return HtmlResponse.create_response(response.status_code, None)
        else:
            return HtmlResponse.create_response(200, response.text.strip())
    except Exception as e:
        print(e)
        return HtmlResponse.create_response(500, None)


def generate_testcases(url_list, func):
    for i in range(len(url_list)):
        url = url_list[i]
        parsed_data = func(url)
        raw_html = get_html_from_url(url)
        print(f'parsed_data: {parsed_data}')
        print(f'raw_html: {raw_html.data}')
        filename = f'{func.__name__}_testcase_{i}'
        save_html(f'{filename}.html', raw_html.data)
        save_json(f'{filename}.json', parsed_data)


def save_html(filename, content):
    directory = './testcases'  # 数据保存的目录
    filepath = directory + '/' + filename  # 构建完整的文件路径

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)  # 将内容写入文件


def save_json(filename, data):
    directory = './testcases'  # 数据保存的目录
    filepath = directory + '/' + filename  # 构建完整的文件路径

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(data, file)  # 将数据以 JSON 格式保存到文件中


