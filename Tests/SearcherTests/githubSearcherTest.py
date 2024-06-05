import unittest
from ExternalSearchers import github_searcher


class TestGithubSearcher(unittest.TestCase):

    def test_search_advisories_by_id(self):
        github_list = ['CVE-2023-1495',  #多个匹配，其中只有一个符合条件
                       'CVE-2022-21188',  #搜索不到
                       'CVE-2024-28103',  #单个匹配
                       'GHSA-5cxf-xx9j-54jc',  #单个匹配
                       'CVE-2024-4886 '  #单个匹配
                       ]
        for cve_id in github_list:
            github_searcher.advisories_search_by_id(cve_id)

    def test_search_advisories(self):
        github_searcher.advisories_search()

    if __name__ == '__main__':
        unittest.main()
