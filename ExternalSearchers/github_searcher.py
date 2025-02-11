import logging
import time

import requests
import re
import base64

from bs4 import BeautifulSoup

# from RefPageParsers.github_parser import commits_parse
# from RefPageParsers.github_parser import commit_parse
from RefPageParsers.github_parser import advisory_parse
from RefPageParsers.github_parser import github_url_transfer
from mongoDB.mongoUtils import insert_or_update_by_cve_id

headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': 'application/json, application/vnd.github+json',
    # 如果还需要使用graphQL，请在这里附上github token
    'Connection': 'keep-alive'
}
max_retries = 5
collection_name = 'githubAdvisories'


def get_github_blob(url):
    blob_response = requests.request("GET", url, headers={'User-Agent': 'baidu'})
    if blob_response and blob_response.json()['content']:
        content = base64.b64decode(blob_response.json()['content']).decode('utf-8')
        content = re.sub(r'#+', '', content)
        return content
    else:
        return None


def get_github_tree(url):
    tree_response = requests.request("GET", url, headers={'User-Agent': 'baidu'})
    tree_nodes = []
    if tree_response and tree_response.json()['tree']:
        tree = tree_response.json()
        for tree_node in tree['tree']:
            tree_nodes.append(
                {
                    'path': tree_node['path'],
                    'url': tree_node['url']
                }
            )
        return tree_nodes
    else:
        return None


# 获取一个gitlog里面的全部信息
def gitlog_search(url):
    # 传入的url应该是一个github仓库链接
    repos_url = github_url_transfer(url) + "/contents/"
    response = requests.request("GET", repos_url, headers={'User-Agent': 'baidu'})
    log_format = re.compile('.*[C|c][H|h][A|a][N|n][G|g][E|e][L|l][O|o][G|g].*')
    temp_list = re.findall(log_format, response.text)
    if temp_list:
        def get_change_log(ele):
            return 'changelog' in str(ele['name']).lower()

        result = list(filter(get_change_log, response.json()))
        content_list = []
        for ele in result:
            name = ele['name']
            html_url = ele['html_url']
            git_url = ele['git_url']
            if ele['type'] == 'file':
                content = get_github_blob(git_url)
                content_list.append(
                    {
                        'name': name,
                        'url': html_url,
                        'content': content
                    }
                )
            elif ele['type'] == 'dir':
                tree = get_github_tree(git_url)
                for tree_node in tree:
                    content = get_github_blob(tree_node['url'])
                    content_list.append(
                        {
                            'name': tree_node['path'],
                            'url': html_url + '/' + tree_node['path'],
                            'content': content
                        }
                    )

        print(content_list)
        return content_list
    else:
        return None


# 获取一个commit里面所有fix相关的commit信息
# def fix_commits_search(url):
#     commits_page = commits_parse(url)
#     fix_message_format = re.compile('^[F|f][I|i][X|x].*')
#     fix_commits_list = []
#     for commits in commits_page:
#         if commits['commit'] is not None and commits['commit']['message'] is not None and re.match(fix_message_format,
#                                                                                                    commits['commit'][
#                                                                                                        'message']) is not None:
#             url = commits['commit']['url']
#             message = commits['commit']['message']
#             if url is not None:
#                 url = url.replace('api.', '').replace('repos/', '').replace('commits', 'commit').replace('git/', '')
#                 commit_detail = commit_parse(url)
#                 fix_commits_list.append({
#                     'message': message,
#                     'content': commit_detail
#                 })
#     print(len(fix_commits_list))
#     print(fix_commits_list)
#     return fix_commits_list


# 根据cve_id的列表爬取advisories对应的数据，然后保存进入advisories的数据库
# 最后返回一个dict，key为cve-id，value为对应的数据
def get_from_advisories_by_cve_list(cve_list):
    data_dict = {}
    if cve_list is None or len(cve_list) == 0:
        return None
    for cve_id in cve_list:
        try:
            data = advisories_search_by_id(cve_id=cve_id)
        except Exception as e:
            print(e)
            continue
        if data is not None:
            # cve编号是利用query条件来进行插入和更新的，此处应该删除掉
            if 'No' in data:
                del data['No']
            insert_or_update_by_cve_id(cve_id=cve_id, collection_name=collection_name, doc=data)
            data_dict[cve_id] = data
        time.sleep(5)
    return data_dict


def advisories_search_by_id(cve_id):
    advisories_base = 'https://github.com/advisories?query='
    advisory_url = advisories_base + cve_id
    retries = 0
    while retries < max_retries:
        try:
            response = advisories_search_by_url(advisory_url)
            # 处理响应
            return response
        except requests.exceptions.ConnectionError:
            logging.info("ConnectionError occurred. Retrying...")
            retries += 1
            time.sleep(1)  # 可以调整重试间隔时间，这里设置为1秒

    logging.info("Failed after {} retries.".format(max_retries))
    return None


# 在github advisories里面搜索
def advisories_search_by_url(advisory_url):
    query_idx = advisory_url.find('query=')
    if query_idx == -1:
        print("invalid url pattern!!")
        return None
    cve_id = advisory_url[query_idx + 6:]
    response = requests.request("GET", advisory_url, headers={'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'})
    soup = BeautifulSoup(response.text, "html.parser")
    cve_id_list = soup.find_all('div', class_='mt-1 text-small color-fg-muted')
    cve_find_or_not = False
    for cve in cve_id_list:
        # 找到了对应cve-id的链接
        if cve.find_next('span').text.strip() == cve_id:
            cve_find_or_not = True
            cve_url = cve.find_parent().find('a', class_='Link--primary v-align-middle no-underline h4 '
                                                         'js-navigation-open').get('href')
            cve_url = 'https://github.com' + cve_url
            res = advisory_parse(cve_url)
            return res
    # 这个里面没有对应的cve
    if not cve_find_or_not:
        print('Cannot find github advisory of cve:' + cve_id + '!')
        return None


def graphql_search(query):
    url = 'https://api.github.com/graphql'
    data = {
        'query': query
    }

    # 发送GraphQL请求
    response = requests.post(url, json=data, headers=headers)

    # 处理响应数据
    result = response.json()
    return result


def advisories_search():
    # 构建GraphQL查询
    query = '''
    query {
        securityAdvisories(first:20, publishedSince: "2023-01-01T00:00:00Z"){
            edges{
                node{
                    id
                    ghsaId
                    classification
                    cvss{
                        score
                        vectorString
                    } 
                    identifiers{
                        type
                        value
                    }
                    description
                    origin
                    permalink
                    publishedAt
                    updatedAt
                    references{
                        url
                    }
                    severity
                    summary
                    vulnerabilities(first:10){
                        edges{
                            node{
                                firstPatchedVersion{
                                    identifier
                                }
                                package{
                                    ecosystem
                                    name
                                }
                                updatedAt
                                vulnerableVersionRange    
                            }
                        }
                    }
                }
            }
        }
    }
    '''

    # 处理响应数据
    result = graphql_search(query)
    if result is not None:
        ret_advisories_list = []
        advisories_list_raw = result['data']['securityAdvisories']['edges']
        for advisory in advisories_list_raw:
            ret_advisories_list.append(advisory['node'])
            print(advisory['node'])
        return ret_advisories_list  # 输出响应结果
    return None


if __name__ == "__main__":
    print(get_from_advisories_by_cve_list(['CVE-2023-50868', 'CVE-2023-50866']))
