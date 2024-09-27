# -*- coding: utf-8 -*-
import datetime
import re
import time
from lxml import etree
import pymongo

from RefPageParsers.parse_driver import parse_url
from Utils.TimeUtils import get_current_time
from Utils.util import get_page_content
from Utils.TimeUtils import compare_dates
from Constants.dbConstants import create_mongo_connection
client = create_mongo_connection()

list_base_url = "https://avd.aliyun.com/nvd/list?page="
search_base_url = "https://avd.aliyun.com/search?q="
detail_base_url = "https://avd.aliyun.com/detail?id=AVD"

mongodb_client = client
db = mongodb_client['local']
cve_collection = db['aliCloud']


def get_all_page_cnt():
    html = get_page_content(list_base_url)
    html_tree = etree.HTML(html)
    pages_str = html_tree.xpath("/html/body/main/div/div/div[2]/div/span/text()")[0]
    # 使用正则表达式提取页数
    match = re.search(r"第\s*(\d+)\s*页\s*/\s*(\d+)\s*页", pages_str)
    total_pages = int(match.group(2))
    return total_pages


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
        # patch_detail = parse_url(para)
        # result_str.append({
        #     'patch_url': str(para),
        #     'service_name': patch_detail.get('service_name'),
        #     'patch_detail': patch_detail.get('detail'),
        #     'time': get_current_time()
        # })
        result_str.append(str(para))
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

    def increment_version(version_list):
        """
        增加版本号。

        参数：
        version_list (list): 整数列表表示的版本号。

        返回：
        list: 增加后的版本号。
        """
        for i in reversed(range(len(version_list))):
            version_list[i] += 1
            if version_list[i] < 10:
                break
            else:
                version_list[i] = 0
                if i == 0:
                    version_list.insert(0, 1)
        return version_list

    def extract_detail_versions(versions_raw):
        """
        从给定的版本范围列表中提取所有版本号。

        参数：
        versions_raw (list): 包含版本范围的列表。

        返回：
        list: 包含所有提取版本号的新列表。
        """
        final_versions = []

        for version in versions_raw:
            # 查找包含From和Up to的版本范围
            match = re.match(r"From\(including\)([\d.]+)-Up to\(excluding\)([\d.]+)", version)

            if match:
                # 提取起始和结束版本号
                start_version = match.group(1)
                end_version = match.group(2)

                # 将版本号分割成整数列表
                start_version_list = list(map(int, start_version.split('.')))
                end_version_list = list(map(int, end_version.split('.')))

                # 生成版本号
                current_version_list = start_version_list.copy()
                while current_version_list < end_version_list:
                    # 将整数列表转成版本字符串
                    current_version = '.'.join(map(str, current_version_list))
                    final_versions.append(current_version)

                    # 增加版本号
                    current_version_list = increment_version(current_version_list)
            else:
                # 如果是单独版本号，直接添加到最终列表
                final_versions.append(version)

        return final_versions

    def convert_versions_to_interval(versions_raw):
        """
        将版本范围列表转换为数学表示。

        参数：
        versions_raw (list): 包含版本范围的列表。

        返回：
        list: 包含数学表示的新列表。
        """
        math_versions = []

        for version in versions_raw:
            # 查找包含From和Up to的版本范围
            match = re.match(r"From\(including\)([\d.]+)-Up to\(excluding\)([\d.]+)", version)

            if match:
                # 提取起始和结束版本号
                start_version = match.group(1)
                end_version = match.group(2)

                # 将起始和结束版本号转换为数学表示
                start_math = f">={start_version}"
                end_math = f"<={end_version}"

                # 将数学表示添加到新列表
                math_versions.append(start_math)
                math_versions.append(end_math)
            else:
                # 如果是单独版本号，直接添加到最终列表
                math_versions.append(version)

        return math_versions

    def merge_versions(data):
        result = {}
        if data:
            for item in data:
                product_name = item.get("产品")
                version_info = item.get("版本")
                impact = item.get("影响面")

                if product_name not in result:
                    result[product_name] = {"software_name": product_name,
                                            "interval_versions": [],
                                            "detail_versions": [],
                                            "raw_versions": []}
                if impact:
                    result[product_name]["raw_versions"].append(impact)
                else:
                    result[product_name]["raw_versions"].append(version_info)
        # 调用函数并打印结果
        for product_item in result.values():
            print(f"product 的类型: {type(product_item)}")
            product_item["detail_versions"] = extract_detail_versions(product_item["raw_versions"])
            product_item["interval_versions"] = convert_versions_to_interval(product_item["raw_versions"])
        return list(result.values())

    return merge_versions(data)


def crawl_url(url, start_time=None, end_time=None):
    # 某一页的全部数据，html格式
    html = get_page_content(url)
    # 用正则表达式找到html里面需要用的格式
    contents = get_cve_content(html)
    # 根据本页最后一个条目的时间来判断这一页是否可以跳过
    earliest_time_in_page = contents[len(contents) - 1][3].strip()
    if end_time is not None and earliest_time_in_page is not None and compare_dates(earliest_time_in_page, end_time) == 1:
        # 本页最后一个时间（最早时间）在end_time之后，这一页都可以跳过
        return
    for content in contents:
        content = list(content)
        for i in range(0, len(content)):
            content[i] = content[i].strip()  # 去除字符串中的空格
        nvd_no = str(content[0])
        detail_url = detail_base_url + nvd_no[3:]
        detail_html = get_page_content(detail_url)
        detail_html_etree = etree.HTML(detail_html)
        cve_time = content[3]
        if end_time is not None and compare_dates(end_time, cve_time) == -1:
            continue
        if start_time is not None and compare_dates(cve_time, start_time) == -1:
            return -1
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
                'cve_published_time': content[3],
                'cve_modified_time': content[3],
                'crawl_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'rate': content[4],
                'source_url': detail_url,
                'description': content[5],
                # 'ref_link': content[6],
                'affected_software': content[6],
                'reference': content[7]
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


def crawl_by_pages(start_page_num, end_page_num):
    global get_cve_patch_details
    for page_num in range(start_page_num, end_page_num):
        print("正在爬取第" + str(page_num) + "页数据")
        # 某一页的url
        url = list_base_url + str(page_num)
        crawl_url(url)
        time.sleep(3)


def crawl_one_by_cve_id(cve_id):
    global get_cve_patch_details
    url = search_base_url + cve_id
    crawl_url(url)


def alicloud_crawl_all():
    for page_num in range(1, get_all_page_cnt()):
        print("正在爬取第" + str(page_num) + "页数据")
        # 某一页的url
        url = list_base_url + str(page_num)
        crawl_url(url)
        time.sleep(3)


def alicloud_crawl_by_time(start_time=None, end_time=None):
    for page_num in range(1, get_all_page_cnt()):
        print("正在爬取第" + str(page_num) + "页数据")
        # 某一页的url
        url = list_base_url + str(page_num)
        if crawl_url(url, start_time, end_time) == -1:
            if end_time is None:
                print(f'截止到{start_time}的阿里云数据已经爬取完成!')
            else:
                print(f'{start_time}到{end_time}之间的阿里云数据已经爬取完成!')
            return
        time.sleep(3)


if __name__ == "__main__":
    crawl_by_pages(1, 10)
    # crawl_one_by_cve_id("CVE-2020-13992")
    # crawl_one_by_cve_id("CVE-2020-15073")
