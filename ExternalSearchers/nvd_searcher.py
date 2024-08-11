import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from RefPageParsers.github_parser import github_parse
from Utils.TimeUtils import get_current_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from Utils.util import parse_patch_url
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
# from RefPageParsers.windows_parser import win_parser

headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': '*',
    'Connection': 'keep-alive'
}

cve_pattern = re.compile("(cve|CVE)-[0-9]{4}-[0-9]{4,}$")


def selenium_parse(url):
    driver = webdriver.Chrome()
    # 打开网页
    driver.get(url)
    buttons = [driver.find_elements(By.CSS_SELECTOR, "[data-cpe-list-toggle]"),
               driver.find_elements(By.CSS_SELECTOR, "[data-cpe-range-toggle]")]
    for button_list in buttons:
        for button in button_list:
            button.click()
    time.sleep(5)
    cpe_lists = driver.find_elements(By.CSS_SELECTOR, "[data-list-cpes]")
    if cpe_lists is None:
        return None
    detail_versions = []
    for element in cpe_lists:
        cpes = element.find_elements(By.TAG_NAME, 'li')
        temp_list = []
        for cpe in cpes:
            version = cpe.text
            idx = version.find('\n')
            if idx != -1:
                # 说明是被修改过的格式
                version = version[idx + 1:]
            temp_list.append(version)
        detail_versions.append(list(set(temp_list)))
    driver.quit()
    return detail_versions


def modify_software_version(version):
    version = version.replace("versions", "")
    version = version.replace(" ", "")
    # 代表是否存在区间
    range_num = 0
    if version.find("from") != -1:
        range_num = range_num + 1
        version = version.replace("from", ">")
    if version.find("upto") != -1:
        range_num = range_num + 1
        version = version.replace("upto", "<")
    version = version.replace("(including)", "=")
    version = version.replace("(excluding)", "")
    # 有两个区间，此时需要用逗号隔开，在<号之前插入一个逗号
    if range_num == 2:
        idx_to_insert = version.find("<")
        version = version[0:idx_to_insert] + "," + version[idx_to_insert:]
    return version


def search_nvd_using_cve_id(cve_id):
    # 先按照正则表达式判断一下cve_id是否是合法的
    if not re.match(cve_pattern, cve_id):
        print('invalid cve-id!')
        return None
    url = 'https://nvd.nist.gov/vuln/detail/' + cve_id
    return search_nvd_using_url(url)


def transfer_nvd_time(date_string):
    input_format = "%m/%d/%Y"  # 输入日期的格式
    output_format = "%Y-%m-%d"  # 输出日期的格式
    # 将输入日期字符串解析为 datetime 对象
    date = datetime.strptime(date_string, input_format)

    # 将 datetime 对象转换为输出日期字符串
    output_date_string = date.strftime(output_format)

    return output_date_string


def search_nvd_using_url(url):
    cve_id_idx = re.search(cve_pattern, url)
    if cve_id_idx is None:
        return None
    cve_id = url[cve_id_idx.span()[0]:cve_id_idx.span()[1]]
    response = requests.request("GET", url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    detail_versions = selenium_parse(url)
    title = soup.find('title').text.strip()
    # cve-id合法，但是并不能找到对应的cve
    if title == 'NVD - Invalid Parameters':
        print('no such cve!')
        return None

    warn = soup.find(id="vulnShowWarningDiv")
    # 假设每一个页面的description标签只有一个，并且在title标签后一个
    description = soup.find(id="vulnDescriptionTitle").find_next_sibling('p', attrs={'data-testid': True}).text.strip()
    # 判断一下是否rejected，如果是的话返回reject信息
    if warn:
        slogan = warn.find(class_='h4Size').text.strip()
        if slogan == 'Rejected':
            print('REJECTED!CVE has been marked "REJECT" in the CVE List. These CVEs are stored in the NVD, but do not '
                  'show up in search results.')
            print(description)
            return None

    # 到这里说明这是一个有内容且正常的界面，代表cve是有效的
    # 这里假设score在class_='severityDetail'这个标签的正后面并且只有一个
    score = soup.find(id="Vuln3CvssPanel").find(class_='severityDetail').find_next('a').text
    badge_list = soup.find_all(class_='badge')
    # 查找具有 data-testid="vuln-published-on" 的字段
    published_date = soup.find(attrs={"data-testid": "vuln-published-on"})
    if published_date is not None:
        published_date = transfer_nvd_time(published_date.text)
    modified_date = soup.find(attrs = {"data-testid", "vuln-last-modified-on"})
    if modified_date is not None:
        modified_date = transfer_nvd_time(modified_date.text)
    patch_url_list = []
    patch_list = []
    third_party_advisory = []
    vendor_advisory = []
    exploit = []

    software_text_list = soup.find_all('pre')
    software_list_dict = {}
    for i in range(0, len(software_text_list)):
        software = software_text_list[i]
        software_text = software.text
        if software_text.startswith('OR'):
            temp_list = software_text.split('\n')
            for temp in temp_list:
                temp = temp.lstrip()
                if temp.startswith("*cpe:2.3:a:"):  # cpe2.3
                    start_idx = 11
                elif temp.startswith("*cpe:/a:"):  # cpe2.2
                    start_idx = 8
                else:
                    print("unsupported cpe version!")
                    continue
                software_with_version = temp[start_idx:]

                # 第一个空格之后是版本，之前是软件名称
                space_idx = temp.find(' ')
                software_name = temp[start_idx:space_idx] if space_idx != -1 else temp[start_idx:]
                # 说明有版本号
                curr_version = temp[space_idx + 1:] if space_idx != -1 else None
                # 如果这个软件的信息还没建立，先建立一下
                if software_name not in software_list_dict:
                    software_list_dict[software_name] = {
                        "software_name": software_name,
                        "interval_versions": [],
                        "detail_versions": detail_versions[i],
                        "raw_versions": []
                    }
                # 整合软件版本信息
                if curr_version is not None:
                    # 将版本信息修改为>=号和<=号的修改
                    curr_version = modify_software_version(curr_version)
                    software_list_dict[software_name]["interval_versions"].append(curr_version)
                    software_list_dict[software_name]["raw_versions"].append(software_with_version)

    # 此时的dict已经存放了这个网页下面所有软件和版本信息，key为软件名，版本信息为value，将其转换为数组
    software_list = [value for value in software_list_dict.values()]

    for badge in badge_list:
        curr_href = badge.find_parent('tr').find('a').get('href')
        # 如果是空的就不管他
        if not curr_href:
            continue
        if badge.text == 'Patch':
            patch_url_list.append(curr_href)
        if badge.text == 'Third Party Advisory':
            third_party_advisory.append(curr_href)
        if badge.text == 'Vendor Advisory':
            vendor_advisory.append(curr_href)
        if badge.text == 'Exploit':
            exploit.append(curr_href)

    nvd_detail = {
        'No': cve_id,
        'title': title,
        'description': description,
        'score': score,
        'source_url': url,  # 网页的链接 url
        'cve_published_time': published_date,
        'cve_modified_time': modified_date,
        'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'affected_software': software_list,
    }

    # 如果我们可以找到patch就对patch_list进行解析并返回
    if patch_url_list:
        for patch_url in patch_url_list:
            patch_detail = parse_patch_url(patch_url)
            patch_list.append({
                'patch_url': patch_url,
                'service_name': patch_detail['service_name'],
                'patch_detail': patch_detail['detail'],
                'time': get_current_time()
            })

    nvd_detail['patch_list'] = patch_list
    nvd_detail['third_party_list'] = third_party_advisory
    nvd_detail['vendor_list'] = vendor_advisory
    nvd_detail['exploit'] = exploit
    print(nvd_detail)
    return nvd_detail


# nvd_list = ['CVE-2022-1',  # 无效的
#             'CVE-2022-28066',  # 被拒绝的
#             'CVE-2020-19952',  # github的patch
#             'CVE-2023-43746',  # 没有patch
#             'CVE-2023-36569'  # 微软的patch
#             ]

# if __name__ == "__main__":
#     nvd_list = [
#                 'https://nvd.nist.gov/vuln/detail/CVE-2021-41094'
#                 ]
#     for cve_id in nvd_list:
#         nvd_detail = search_nvd_using_url(cve_id)
#         print(nvd_detail)

# search_nvd_using_url('https://nvd.nist.gov/vuln/detail/CVE-2023-50868')
