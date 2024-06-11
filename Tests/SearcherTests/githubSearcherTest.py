import unittest
from ExternalSearchers import github_searcher
from ExternalSearchers.github_searcher import graphql_search
from Tests.Utils.test_utils import generate_testcases
from Tests.Utils.advisories_utils import generate_url_list_for_github_advisories, generate_testcases_for_advisories


class TestGithubSearcher(unittest.TestCase):

    def test_search_advisories_by_id(self):
        advisories_list = ['https://github.com/advisories?query=CVE-2023-1495',  # 多个匹配，其中只有一个符合条件
                           'https://github.com/advisories?query=CVE-2022-21188',  # 搜索不到
                           'https://github.com/advisories?query=CVE-2024-28103',  # 单个匹配
                           'https://github.com/advisories?query=GHSA-5cxf-xx9j-54jc',  # 单个匹配
                           ]
        advisories_testcases = []
        generate_testcases(advisories_list, advisories_testcases, github_searcher.advisories_search_by_url)

    def test_search_advisories(self):
        parsed_data = github_searcher.advisories_search()
        url_list = generate_url_list_for_github_advisories()
        advisories_testcases = []
        generate_testcases_for_advisories(url_list, advisories_testcases, parsed_data)

    if __name__ == '__main__':
        unittest.main()
