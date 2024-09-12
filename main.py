# -*- coding: utf-8 -*-
import re
import time
import pandas
import requests
from lxml import etree
from random import randint
from Constants.dbConstants import client

START_PAGE_NUM = 1
END_PAGE_NUM = 2
list_base_url = 'https://avd.aliyun.com/nvd/list?type=应用程序&page='
detail_base_url = 'https://avd.aliyun.com/detail?id=AVD'


def get_page_content(url):
    user_agent = [
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    try:
        response = requests.get(url, headers={'User-Agent': user_agent[randint(0, 1)]})
        if response.status_code == 200:
            return response.text
        return
    except Exception:
        return


def get_cve_content(res):
    match = re.compile(
        '<tr>.*?target="_blank">(.*?)' +
        '</a></td>.*?<td>(.*?)' +
        '</td>.*?<button.*?>(.*?)' +
        '</button>.*?nowrap="nowrap">(.*?)' +
        '</td>.*?<button.*?>(.*?)' +
        '</button>.*?</tr>'
        , re.S)
    contents = re.findall(match, res)
    return contents


def get_cve_description(cve_etree):
    result_str = ""
    for para in cve_etree.xpath("/html/body/div[3]/div/div[1]/div[2]/div[1]/div/text()"):
        result_str = result_str + str(para)
    return result_str.strip()


def get_cve_ref_link(cve_etree):
    result_str = ""
    for para in cve_etree.xpath("/html/body/div[3]/div/div[1]/div[2]/div[3]/table/tbody/tr/td/a/@href"):
        result_str = result_str + str(para) + " "
    return result_str.strip()


def main():
    mongodb_client = client
    db = mongodb_client['local']
    collection = db['CVE']
    result_df = pandas.DataFrame(
        data=None,
        columns=['No.', 'name', 'type', 'time', 'rate', 'description', 'ref link']
    )
    for page_num in range(START_PAGE_NUM, END_PAGE_NUM):
        print("正在爬取第" + str(page_num) + "页数据")
        content_list = []
        # 某一页的url
        url = list_base_url + str(page_num)
        # 某一页的全部数据，html格式
        html = get_page_content(url)
        # 用正则表达式找到html里面需要用的格式
        for content in get_cve_content(html):
            content = list(content)
            for i in range(0, len(content)):
                content[i] = content[i].strip()  # 去除字符串中的空格
            nvd_no = str(content[0])
            # 获取具体漏洞页的信息
            detail_html = get_page_content(detail_base_url + nvd_no[3:])
            # 用etree.HTML解析html数据
            detail_html_etree = etree.HTML(detail_html)
            cve_description = str(get_cve_description(detail_html_etree))
            cve_ref_link = str(get_cve_ref_link(detail_html_etree))
            if "开源" in cve_description or "github.com" in cve_ref_link:
                try:
                    content.append(cve_description)
                    content.append(cve_ref_link)
                    cve_info_dict = {
                        'No.': content[0],
                        'name': content[1],
                        'type': content[2],
                        'time': content[3],
                        'rate': content[4],
                        'description': content[5],
                        'ref_link': content[6],
                    }
                    # content_list.append(content)
                    collection.insert_one(cve_info_dict)
                    print("已将CVE编号为" + str(content[0]) + "的漏洞存入数据库")
                except :
                    print("读取与存入CVE编号为" + str(content[0]) + " 的信息时出现异常")
        time.sleep(3)


if __name__ == "__main__":
    main()
