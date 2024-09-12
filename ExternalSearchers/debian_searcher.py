import requests
from bs4 import BeautifulSoup

from Utils.TimeUtils import get_current_time
from Utils.util import parse_patch_url
from mongoDB.mongoUtils import insert_or_update_by_cve_id


collection_name = 'debian'


# 根据cve_id的列表爬取debian对应的数据，然后保存进入debian的数据库
# 最后返回一个dict，key为cve-id，value为对应的数据
def get_from_debian_by_cve_list(cve_list):
    data_dict = {}
    if cve_list is None or len(cve_list) == 0:
        return None
    for cve_id in cve_list:
        data = debian_search_by_cve_id(cve_id=cve_id)
        if data is not None:
            insert_or_update_by_cve_id(cve_id=cve_id, collection_name=collection_name, doc=data)
            print(data)
            data_dict[cve_id] = data
    return data_dict


def debian_search_by_cve_id(cve_id):
    base_url = 'https://security-tracker.debian.org/tracker/'
    url = base_url + cve_id
    # 发起 GET 请求获取页面内容
    response = requests.request("GET", url, headers={'User-Agent': 'baidu'})
    if response.status_code != 200:
        print('Failed to retrieve the webpage. Status code:', response.status_code)
        return None
    # 解析 HTML 内容
    soup = BeautifulSoup(response.content, 'html.parser')

    # 查找所有 <pre> 元素
    pre_elements = soup.find('pre')
    if pre_elements is None:
        print('Failed to parse debian page：' + '没有Notes列表！')
        return None
    a_elements = pre_elements.find_all('a')
    if a_elements is None:
        print('Failed to parse debian page：' + '没有超链接！')
        return None
    ref_link_list = []
    patch_list = []
    for element in a_elements:
        patch_url = element.text
        ref_link = patch_url
        if element.next_sibling and element.next_sibling.string:
            ref_link = ref_link + element.next_sibling.string.strip()
        if element.previous_sibling and element.previous_sibling.string:
            ref_link = element.previous_sibling.string.strip() + ref_link
        if ref_link.lower().startswith('fixed by:') or ref_link.lower().startswith('upstream patch'):
            patch_detail = parse_patch_url(patch_url)
            patch_list.append({
                'patch_url': patch_url,
                'service_name': patch_detail['service_name'],
                'patch_detail': patch_detail['detail'],
                'time': get_current_time()
            })
        ref_link_list.append(ref_link)
    return {
        'No': cve_id,
        'source_url': url,
        'ref_links': ref_link_list,
        'patch_list': patch_list
    }


# if __name__ == '__main__':
#     print(get_from_debian_by_cve_list(['CVE-2023-50868', 'CVE-2023-50866']))
