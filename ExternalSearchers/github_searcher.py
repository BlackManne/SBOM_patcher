import requests
import re
import base64

from bs4 import BeautifulSoup

from RefPageParsers.github_parser import github_parse
from RefPageParsers.github_parser import commits_parse
from RefPageParsers.github_parser import commit_parse
from RefPageParsers.github_parser import advisory_parse
from Utils.util import github_url_transfer

headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': 'application/json, application/vnd.github+json',
    'Authorization': 'Bearer '
                     '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',
    'Connection': 'keep-alive'
}
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
def fix_commits_search(url):
    commits_page = commits_parse(url)
    fix_message_format = re.compile('^[F|f][I|i][X|x].*')
    fix_commits_list = []
    for commits in commits_page:
        if commits['commit'] is not None and commits['commit']['message'] is not None and re.match(fix_message_format,
                                                                                                   commits['commit'][
                                                                                                       'message']) is not None:
            url = commits['commit']['url']
            message = commits['commit']['message']
            if url is not None:
                url = url.replace('api.', '').replace('repos/', '').replace('commits', 'commit').replace('git/', '')
                commit_detail = commit_parse(url)
                fix_commits_list.append({
                    'message': message,
                    'content': commit_detail
                })
    print(len(fix_commits_list))
    print(fix_commits_list)
    return fix_commits_list


# 在github advisories里面搜索
def advisories_search_by_id(cve_id):
    advisories_base = 'https://github.com/advisories?query='
    advisory_url = advisories_base + cve_id
    response = requests.request("GET", advisory_url, headers={'User-Agent': 'baidu'})
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
            print(advisory_parse(cve_url))
            break
    # 这个里面没有对应的cve
    if not cve_find_or_not:
        print('Cannot find github advisory of cve:' + cve_id + '!')


def advisories_search():
    url = 'https://api.github.com/graphql'
    # 构建GraphQL查询
    query = '''
    query {
        securityAdvisories(first:20){
            edges{
                node{
                    classification
                    cvss{
                        score
                        vectorString
                    }
                    ghsaId
                    id 
                    identifiers{
                        type
                        value
                    }
                    origin
                    permalink
                    publishedAt
                }
            }
        }
    }
    '''

    data = {
        'query': query
    }

    # 发送GraphQL请求
    response = requests.post(url, json=data, headers=headers)

    # 处理响应数据
    result = response.json()
    return result # 输出响应结果


if __name__ == "__main__":
    # url_list = ["https://github.com/pyscript/pyscript/commits/main",
    #             # "https://github.com/pyscript/pyscript/commits",
    #             # "https://github.com/pyscript/pyscript/commits/fpliger/example-panel-worker"
    #             ]
    # for url in url_list:
    #     fix_commits_search(url)
    # advisories_search('CVE-2023-1495')
    print(advisories_search())
    advisories_list = advisories_search()['data']['securityAdvisories']['edges']
    for advisory in advisories_list:
        print(advisory)
