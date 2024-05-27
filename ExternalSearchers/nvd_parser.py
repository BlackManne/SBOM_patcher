import re
import requests
from bs4 import BeautifulSoup
from RefPageParsers.github_parser import github_parse
# from RefPageParsers.windows_parser import win_parser

headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': '*',
    'Connection': 'keep-alive'
}


def search_nvd(cve_id):
    # 先按照正则表达式判断一下cve_id是否是合法的
    cve_pattern = re.compile("(cve|CVE)-[0-9]{4}-[0-9]{4,}$")
    if not re.match(cve_pattern, cve_id):
        print('invalid cve-id!')
        return None
    url = 'https://nvd.nist.gov/vuln/detail/' + cve_id
    response = requests.request("GET", url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
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
    patch_url_list = []
    third_party_advisory = []
    vendor_advisory = []
    exploit = []

    software_text_list = soup.find_all('pre')
    software_list_dict = {}
    for software in software_text_list:
        software_text = software.text
        if software_text.startswith('OR'):
            temp_list = software_text.split('\n')
            for temp in temp_list:
                temp = temp.lstrip()
                if temp.startswith("*cpe:2.3:a:"): #cpe2.3
                    start_idx = 11
                elif temp.startswith("*cpe:/a:"):  #cpe2.2
                    start_idx = 8
                else:
                    print("unsupported cpe version!")
                    continue
                software_with_version = temp[start_idx:]
                print(software_with_version)

                # 第一个空格之后是版本，之前是软件名称
                space_idx = temp.find(' ')
                software_name = temp[start_idx:space_idx] if space_idx != -1 else temp[start_idx:]
                # 说明有版本号
                curr_version = temp[space_idx + 1:] if space_idx != -1 else None
                # 如果这个软件的信息还没建立，先建立一下
                if software_name not in software_list_dict:
                    software_list_dict[software_name] = {
                        "software_name": software_name,
                        "versions": [],
                        "versions_raw": []
                    }
                # 整合软件版本信息
                if curr_version is not None:
                    software_list_dict[software_name]["versions"].append(curr_version)
                    software_list_dict[software_name]["versions_raw"].append(software_with_version)

    # 此时的dict已经存放了这个网页下面所有软件和版本信息，key为软件名，版本信息为value，将其转换为数组
    software_list = [value for value in software_list_dict.values()]
    print(software_list)

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
        'affected_software': software_list
    }
    # 如果我们可以找到patch就对patch_list进行解析并返回
    if patch_url_list:
        nvd_detail['patch_list'] = []
        for patch_url in patch_url_list:
            patch_detail = parse_nvd(patch_url)
            nvd_detail['patch_list'].append({
                'patch_url': patch_detail,
                'service_name': patch_detail['service_name'],
                'patch_detail': patch_detail['detail']
            })
    # 如果找不到的话就返回vendor advisory和third party advisory
    # exploit也是个重要的格式，代表在哪里发现了漏洞
    else:
        nvd_detail['third_party_list'] = third_party_advisory
        nvd_detail['vendor_list'] = vendor_advisory
        nvd_detail['exploit'] = exploit
    print(nvd_detail)
    return nvd_detail


def parse_nvd(url):
    patch_detail = {}
    # 根据传入的patch url解析，调用不同的parse函数
    if re.match("https://github.com/.+", url):
        github_detail = github_parse(url)
        patch_detail['detail'] = github_detail['detail']
        patch_detail['service_name'] = github_detail['service_name']
    # elif re.match("https://msrc.microsoft.com/.+", url):
    #     nvd_detail['detail'] = win_parser.parse(url)
    #     nvd_detail['service_name'] = 'microsoft'
    else:
        print('no supported parser for url:' + url)
        patch_detail['detail'] = 'NOT SUPPORTED URL!!'
        patch_detail['service_name'] = None
    return patch_detail


# nvd_list = ['CVE-2022-1',  # 无效的
#             'CVE-2022-28066',  # 被拒绝的
#             'CVE-2020-19952',  # github的patch
#             'CVE-2023-43746',  # 没有patch
#             'CVE-2023-36569'  # 微软的patch
#             ]

# 可以使用的nvd_list
# nvd_list = ['CVE-2023-37582',
#             'CVE-2020-19952',
#             'CVE-2023-43746',
#             'CVE-2023-36568'
#             ]
# for cve_id in nvd_list:
#     search_nvd(cve_id)

search_nvd('CVE-2023-37582')