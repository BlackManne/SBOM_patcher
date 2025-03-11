import requests
import subprocess
from RefPageParsers.github_parser import headers

base_url = 'https://api.github.com/repos/torvalds/linux/'
headers['Accept'] = 'application/json, application/vnd.github+json'


def get_commit_info_for_llm(commit_id):
    detail_url = base_url + 'commits/' + commit_id
    payload = {}
    response = requests.request("GET", detail_url, headers=headers, data=payload)
    commit_info = response.json()
    return commit_info


def get_file_content_for_llm(commit_id, file_name):
    detail_url = base_url + 'contents/' + file_name + '?ref=' + commit_id
    payload = {}
    response = requests.request("GET", detail_url, headers=headers, data=payload)
    content_info = response.json()
    if content_info is None or content_info['content'] is None:
        print(f'获取{commit_id}commit的{file_name}文件时结果为空')
        return None
    return content_info['content']


# def get_compare_for_llm(base_id, head_id, file_name):
#     detail_url = base_url + 'compare/' + base_id + '...' + head_id
#     payload = {}
#     response = requests.request("GET", detail_url, headers=headers, data=payload)
#     compare_info = response.json()
#     if compare_info is None or compare_info['files'] is None:
#         print(f'获取{base_id}commit和{head_id}commit的diff信息时结果为空')
#         return None
#     for file in compare_info['files']:
#         if file['filename'] == file_name:
#             return file['patch']
#     # 如果没有找到对应名字的文件，说明这两个commit该文件没有任何差别
#     return None
#
#
# def get_git_diff_by_cmd(commit1, file1_path, commit2, file2_path):
#     try:
#         # 调用 git diff 命令获取差异信息
#         result = subprocess.run(
#             ["git", "diff", f"{commit1}:{file1_path}", f"{commit2}:{file2_path}"],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             check=True,
#             text=True
#         )
#         # 获取标准输出结果
#         diff_output = result.stdout
#         return diff_output
#     except subprocess.CalledProcessError as e:
#         print(f"Error occurred while running git diff: {e.stderr}")
#         return None
