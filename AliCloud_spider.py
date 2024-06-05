# -*- coding: utf-8 -*-
import json
import re
import time
from lxml import etree
import pymongo

from RefPageParsers import github_parser
from RefPageParsers import apache_parser
from RefPageParsers.parseDriver import parse_url
from Utils.TimeUtils import get_current_time
from Utils.util import get_page_content
from Utils.WebsiteEnum import WebsiteFormat

START_PAGE_NUM = 1
END_PAGE_NUM = 10
list_base_url = 'https://avd.aliyun.com/nvd/list?type=WEB应用&page='
detail_base_url = 'https://avd.aliyun.com/detail?id=AVD'


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


# def get_cve_ref_link(cve_etree):
#     result_str = []
#     for para in cve_etree.xpath("/html/body/div[3]/div/div[1]/div[2]/div[3]/table/tbody/tr/td/a/@href"):
#         parse_url(para)
#         result_str.append(str(para))
#     return result_str

def get_cve_patch_details(cve_etree):
    result_str = []
    for para in cve_etree.xpath("/html/body/div[3]/div/div[1]/div[2]/div[3]/table/tbody/tr/td/a/@href"):
        patch_detail = parse_url(para)
        result_str.append({
            'patch_url': str(para),
            'service_name': patch_detail.get('service_name'),
            'patch_detail': patch_detail.get('detail'),
            'time': get_current_time()
        })
    return result_str


def get_cve_affect_sw(cve_etree):
    table = cve_etree.find('.//table[@class="table"]')
    if table is None:
        return
    # 获取表头 /html/body/div[3]/div/div[1]/div[2]/div[4]/table
    headers = [header.text for header in table.xpath('/html/body/div[3]/div/div[1]/div[2]/div[4]/table/thead/tr['
                                                     '@class="border-bottom"]/td')]
    headers = headers[1:]

    # 获取表格数据
    data = []
    rows = table.xpath("/html/body/div[3]/div/div[1]/div[2]/div[4]/table/tbody/tr")
    for row in rows:
        cols = row.xpath('.//td[@class="bg-light"]')
        cols_new = []
        if cols:
            for i in range(len(cols)):
                if i == 2:
                    cols[i] = cols[i].xpath(".//a")[0].text.strip()
                    cols_new.append(cols[i])
                elif i == 4:
                    cols[i] = cols[i].xpath(".//b")
                    if cols[i]:
                        cols[i] = ''.join([text.strip() for text in cols[i][0].itertext()])
                    else:
                        cols[i] = ""
                elif i == 5:
                    cols[i] = cols[i].xpath(".//b")
                    if cols[i]:
                        cols[i] = ''.join([text.strip() for text in cols[i][0].itertext()])
                    else:
                        cols[i] = ""
                    cols_new.append(cols[i - 1] + '-' + cols[i])
                else:
                    cols_new.append(cols[i].text.strip())
            data.append(dict(zip(headers, cols_new)))

    # 将数据存储为JSON格式
    # 如果没有找到对应的表格 这里会直接返回空
    # result_json = json.dumps(data, ensure_ascii=False)

    def merge_versions(data):
        result = {}
        if data:
            for item in data:
                product_name = item.get("产品")
                version_info = item.get("版本")
                impact = item.get("影响面")

                if product_name not in result:
                    result[product_name] = {"software_name": product_name, "versions": [], "versions_raw": []}
                if impact:
                    result[product_name]["versions_raw"].append(impact)
                else:
                    result[product_name]["versions_raw"].append(version_info)

        return list(result.values())

    return merge_versions(data)


def main():
    global get_cve_patch_details
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
            detail_html = get_page_content(detail_base_url + nvd_no[3:])
            detail_html_etree = etree.HTML(detail_html)
            cve_description = str(get_cve_description(detail_html_etree))
            cve_patch_details = get_cve_patch_details(detail_html_etree)
            # cve_ref_link = get_cve_ref_link(detail_html_etree)
            # json格式
            cve_affect_sw = get_cve_affect_sw(detail_html_etree)
            try:
                content.append(cve_description)
                # content.append(cve_ref_link)
                content.append(cve_affect_sw)
                content.append(cve_patch_details)
                cve_info_dict = {
                    'No': content[0],
                    'name': content[1],
                    'type': content[2],
                    'time': content[3],
                    'rate': content[4],
                    'description': content[5],
                    # 'ref_link': content[6],
                    'affected_software': content[6],
                    'patch_list': content[7]
                }
                # 如果已经找到了对应编号的cve，就不要再存了
                if len(list(cve_collection.find({'No': cve_info_dict['No']}))) == 1:
                    print("\033[92m" + "已有CVE编号为" + str(content[0]) + "的漏洞，不存入" + "\033[0m")
                    continue
                # 没找到说明没有，这个时候再存
                insert_id = cve_collection.insert_one(cve_info_dict).inserted_id
                print("已将CVE编号为" + str(content[0]) + "的漏洞存入数据库")
            except:
                print("\033[31m" + "读取与存入CVE编号为" + str(content[0]) + " 的信息时出现异常" + "\033[0m")
        time.sleep(3)


if __name__ == "__main__":
    mongodb_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = mongodb_client['local']
    cve_collection = db['CVE']
    main()
