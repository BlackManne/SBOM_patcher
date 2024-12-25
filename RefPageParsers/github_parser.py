import os
import re

import requests
from bs4 import BeautifulSoup

from Utils.TokenEncryptor import TokenDecryptor

# 给headers赋值，默认是application/json格式
headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Accept': 'application/json, application/vnd.github+json',
    'Authorization': 'Bearer ' + TokenDecryptor().decrypt_token(),
    'Host': 'api.github.com',
    'Connection': 'keep-alive'
}
payload = {}


def github_url_transfer(url):
    # 把每一个github url转换为调用api.github.com的链接
    return str(url).replace("github.com", "api.github.com/repos")


# commits界面的解析
def commits_parse(url):
    # 判断一下commits后面有没有具体的分支信息
    match_str = re.split('commits', url)
    # 如果是空，直接就是默认url
    url = match_str[0] + 'commits'
    if match_str[1] != '':
        url += ('?sha=' + match_str[1])
    github_url = github_url_transfer(url)
    response = requests.request("GET", github_url, headers=headers, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def commit_parse(url):
    try:
        # 个性化处理commit页面的url
        detail_url = github_url_transfer(url).replace('commit', 'commits')
        headers['Accept'] = 'application/json, application/vnd.github+json'
        response = requests.request("GET", detail_url, headers=headers, data=payload)
        commit_info = response.json()
        # 分别存储message，deletion和addition的数目，改了哪几个文件（文件名称，修改和删除数目，blob_url—）,diff信息
        commit_content = {
            'message': commit_info['commit']['message'].strip(),
            'changes': commit_info['stats'],
            'files': [],
        }
        for file in commit_info['files']:
            file_detail = {
                'filename': file['filename'],
                'additions': file['additions'],
                'deletions': file['deletions'],
                'blob_url': file['blob_url'],
                'diff': None
            }
            # 如果没有任何修改，说明这文件没改，没有diff
            if file['changes'] != 0:
                file_detail['diff'] = file['patch']
            commit_content['files'].append(file_detail)
        print(commit_content)
        return commit_content
    except Exception as e:
        print(e)
        return None


def advisory_parse(url):
    print(url)
    response = requests.request("GET", url, headers={'User-Agent': 'baidu'})
    soup = BeautifulSoup(response.text, "html.parser")
    title_node = soup.find(class_='gh-header-title')
    title = title_node.text.strip() if title_node is not None else soup.find('title').text.split('·')[0]
    filtered_elements = soup.find_all('div', class_='color-fg-muted', string=lambda t: t and t.strip().startswith('CVE-'))
    if filtered_elements is None or len(filtered_elements) == 0:
        cve_id = 'No known CVE'
    else:
        cve_id = filtered_elements[0].text.strip()
    # print(title)
    # 寻找package
    package_node = soup.find(class_='f4 color-fg-default text-bold')
    package = package_node.text.strip() if package_node is not None else None
    package_link = None
    if package_node is not None and package_node.next_sibling.next_sibling is not None:
        temp_node = package_node.next_sibling.next_sibling
        package += temp_node.text.strip()
        # 如果package信息中有界面链接，处理界面链接
        package_link = soup.find(class_='Link Link--muted')
        if package_link is not None:
            package_link = package_link.get('href')
    # 寻找受影响版本和补丁版本
    versions_list = soup.find_all('div', class_='f4 color-fg-default')
    affected_versions = []
    patched_versions = []
    # 如果长度是0说明没找到，这个时候就默认是0就好了
    if len(versions_list) != 0:
        i = 0
        # 寻找受影响版本
        node = versions_list[i]
        affected_versions.append(node.text.strip())
        i = i + 1
        while node.next_sibling is not None:
            node = node.next_sibling
            # 空字符跳过
            if node.text.strip() == '':
                continue
            else:
                affected_versions.append(node.text.strip())
                i = i + 1
        # 寻找补丁版本
        while i < len(versions_list):
            node = versions_list[i]
            patched_versions.append(node.text.strip())
            i = i + 1
            while i < len(versions_list) and node.next_sibling is not None:
                node = node.next_sibling
                if node.text.strip() == '':
                    continue
                else:
                    patched_versions.append(node.text.strip())
                    i = i + 1
                    i = i + 1
    # 默认都初始化为None
    else:
        affected_versions.append('None')
        patched_versions.append('None')
    # 各项字段初始化
    description = ''
    impact = ''
    patches = ''
    workarounds = ''
    reference = []
    more = ''
    patch_reference = []
    commit_format = re.compile('https://github.com/[^/]+/[^/]+/commit/.*')
    # 处理description
    description_parent = soup.find(class_='markdown-body comment-body p-0')
    other_descriptions = description_parent.find_all(['h2', 'h3', 'h4'], recursive=False)

    # 空的话说明没有其他字段，只有description，暴力获得所有<p>
    if not other_descriptions:
        descriptions = description_parent.find_all('p')
        for e in descriptions:
            description += e.text
    else:
        # 在第一个元素之前的都是description
        descriptions = other_descriptions[0].find_previous_siblings('p', recursive=False)
        for e in descriptions:
            if e in other_descriptions:
                break
            description = e.text + description
        # 然后获取的就是其他的元素
        for e in other_descriptions:
            p_list = e.find_next_siblings(recursive=False)
            # 获取实际的信息
            for p in p_list:
                p_detail_list = []
                # 如果是一个ul元素，把里面所有的li都取出来
                father = p
                while p and p.find_next('li') and p.find_next('li').find_parent() == father:
                    p = p.find_next('li').find('a')
                    href = p.get('href') if p is not None else None
                    print(p.text + ' : ' + href)
                    if p:
                        if href:  #有链接添加超链接，否则添加文本
                            p_detail_list.append(href)
                        else:
                            p_detail_list.append(p.text)

                if p in other_descriptions:
                    break

                # 如果不是一个ui列表元素，默认添加自己
                if len(p_detail_list) == 0 and p is not None and p.text is not None:
                    p_detail_list.append(p.text.strip())
                for p_detail in p_detail_list:
                    if p_detail == '':  # 忽略空字符串（包括所有换行符等等）
                        continue
                    if e.text == 'Impact':
                        impact += p_detail
                    elif e.text == 'Patches':
                        patches += p_detail
                    elif e.text == 'Workarounds':
                        workarounds += p_detail
                    elif e.text == 'References':
                        reference.append(p_detail)
                        if re.match(commit_format, p_detail):
                            patch_reference.append(p_detail)
                    elif e.text == 'For more information':
                        more += p_detail
                    else:
                        # 都不满足的话就添加到description字段里面
                        description += '\n' + e.text

    advisory_detail = {
        'No': cve_id,
        'title': title,
        'source_url': url,
        'package': {'name': package, 'link': package_link},
        'affected_versions': affected_versions,
        'patched_versions': patched_versions,
        'description': description,
        'impact': impact,
        'patches': patches,
        'workarounds': workarounds,
        'reference': reference,
        'patch_reference': patch_reference,
        'more': more
    }
    print(advisory_detail)
    return advisory_detail


def issue_parse(url):
    detail_url = github_url_transfer(url)
    headers_for_issue = headers
    headers_for_issue['Accept'] = 'application/vnd.github.VERSION.raw+json'
    response = requests.request("GET", detail_url, headers=headers_for_issue, data=payload)
    content = response.json()
    title = content.get('title')
    created_time = content.get('created_at')
    updated_time = content.get('updated_at')
    closed_time = content.get('closed_at', 'not_closed')
    labels = []
    for label in content.get('labels', []):
        labels.append({'name': label.get('name'), 'description': label.get('description')})
    body = str(content.get('body')).rstrip()
    md_title_format = re.compile(r'###.*\n+')
    res = re.findall(md_title_format, body)
    for s in res:
        new_s = str.replace(s, '### ', '')
        new_s = str.replace(new_s, '\n\n', ' ')
        new_s = str.replace(new_s, '\r\n', ' ')
        body = str.replace(body, s, new_s)
    processed_body = ""
    # 取出每一行的元素，如果是空格的话就不管，不是空格就加上
    for s in body.splitlines():
        if s != '':
            processed_body += s
            processed_body += '\n'
    # 爬取issue相关的comment
    # 可以通过timeline来获得，timeline里面如果有body就代表是有用的信息（一般是一个comment）
    # 如果里面有source代表他有一个来源，这个时候记录source的url，即来源的信息，然后可以通过source的title获取comment内容
    # (真正的内容在source对应的url的body里面)
    timeline_url = detail_url = github_url_transfer(url) + '/timeline'
    response = requests.request("GET", timeline_url, headers=headers_for_issue, data=payload)
    timeline_content = response.json()
    comment_list = []
    requested_reviewers = []
    for time_line in list(timeline_content):
        if not isinstance(time_line, dict):
            # 如果不是字典，跳过
            continue
        # 如果有body，说明是一个comment
        if 'body' in time_line and time_line['body'] is not None:
            comment = time_line['body']
            comment = str.replace(comment, '### ', '')
            comment = str.replace(comment, '\r', '')
            comment_list.append({'type': 'comment', 'content': comment})
        # 评论也是一个issue的情况
        if 'source' in time_line and 'issue' in time_line['source'] is not None:
            issue_comment = time_line['source']['issue']
            if issue_comment is not None:
                issue_url = issue_comment['url']
                comment = issue_comment['title']
                comment_list.append({'type': 'issue', 'content': comment, 'url': issue_url})
        # 元素是一个标签
        if 'label' in time_line and time_line['label'] is not None:
            label_name = time_line['label']['name']
            comment_list.append({'type': 'label', 'content': label_name, 'url': ''})

    issue_detail = {
        'title': title,
        'labels': labels,
        'created_time': created_time,
        'updated_time': updated_time,
        'closed_time': closed_time,
        'content': processed_body,
        'comments': comment_list
    }
    print(issue_detail)
    return issue_detail


def pull_parse(url):
    pull_detail = None
    # pull一共有两种格式，都要分别解析，其中第二次url跟commit格式是一样的，直接按commit处理就可以了
    commit_format = re.compile('https://github.com/[^/]+/[^/]+/pull/[0-9]+/commits/[0-9a-zA-Z]+')
    if re.match(commit_format, url) is not None:
        # 说明是一个commit
        url = re.sub('pull/[0-9]+/', '', url)
        url = re.sub('commits', 'commit', url)
        pull_detail = commit_parse(url)
    else:
        # 转换为issue页面的url
        url = re.sub('pull', 'issues', url)
        pull_detail = issue_parse(url)

    return pull_detail


def file_parse(url):
    # todo 目前只是直接把文件的url返回，看看有没有别的办法
    file_detail = {
        'is_file': 'true',
        'file_url': url
    }

    print(file_detail)
    return file_detail


def github_parse(url):
    github_detail = {
        "detail": None,
        "source": "github",
        "service_name": "github"
    }
    # 根据其中的链接判断是哪一种github页面
    # 格式是https://github.com/{users}/{repos}/xxxx
    commit_format = re.compile('https://github.com/[^/]+/[^/]+/commit/.*')
    advisory_format = re.compile('https://github.com/[^/]+/[^/]+/security/advisories/.+')
    advisories_format = re.compile('https://github.com/advisories/.+')
    issue_format = re.compile('https://github.com/[^/]+/[^/]+/issues/[0-9]+')
    pull_format = re.compile('https://github.com/[^/]+/[^/]+/pull/[0-9]+.*')
    # 文件格式，目前只支持md和pdf格式
    file_format = re.compile('https://github.com/[^/]+/[^/]+/.*\.[(md) | (pdf)]')
    commits_format = re.compile('https://github.com/[^/]+/[^/]+/commits.*')
    if re.match(commit_format, url) is not None:
        github_detail["detail"] = commit_parse(url)
        github_detail["service_name"] += "_commit"
    elif re.match(advisory_format, url) is not None or re.match(advisories_format, url) is not None:
        github_detail["detail"] = advisory_parse(url)
        github_detail["service_name"] += "_advisory"
    elif re.match(issue_format, url) is not None:
        github_detail["detail"] = issue_parse(url)
        github_detail["service_name"] += "_issue"
    elif re.match(pull_format, url) is not None:
        github_detail["detail"] = pull_parse(url)
        github_detail["service_name"] += "_pull"
    elif re.match(file_format, url) is not None:
        github_detail["detail"] = file_parse(url)
        github_detail["service_name"] += "_file"
    elif re.match(commits_format, url) is not None:
        github_detail["detail"] = commits_parse(url)
        github_detail["service_name"] += "_commits"
    else:
        print("NOT SUPPORTED FORMAT!")
    # print(github_detail)
    return github_detail


# if __name__ == "__main__":
#     url_list = [
#         "https://github.com/advisories/GHSA-6qjm-h442-97p9",
#         "https://github.com/advisories/GHSA-fxg5-wq6x-vr4w",
#         "https://github.com/kyverno/kyverno/security/advisories/GHSA-9g37-h7p2-2c6r",
#         "https://github.com/actions/toolkit/security/advisories/GHSA-7r3h-m5j6-3q42",
#         "https://github.com/fastify/github-action-merge-dependabot/security/advisories/GHSA-v5vr-h3xq-8v6w",
#         "https://github.com/git/git/security/advisories/GHSA-j342-m5hw-rr3v",
#         "https://github.com/github/gh-ost/security/advisories/GHSA-rrp4-2xx3-mv29",
#         "https://github.com/cloudflare/cfrpki/security/advisories/GHSA-3pqh-p72c-fj85"]
#     for url in url_list:
#         github_parse(url)
# if __name__ == "__main__":
#         github_parse('https://github.com/advisories/GHSA-m9hc-vxjj-4x6q')
