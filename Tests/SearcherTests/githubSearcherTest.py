import unittest
from ExternalSearchers import github_searcher
from Tests.Utils.test_utils import generate_testcases


class TestGithubSearcher(unittest.TestCase):

    def test_search_advisories_by_id(self):
        advisories_list = ['https://github.com/advisories?query=CVE-2023-1495',  # 多个匹配，其中只有一个符合条件
                           'https://github.com/advisories?query=CVE-2022-21188',  # 搜索不到
                           'https://github.com/advisories?query=CVE-2024-28103',  # 单个匹配
                           'https://github.com/advisories?query=GHSA-5cxf-xx9j-54jc',  # 单个匹配
                           'https://github.com/advisories?query=CVE-2024-4886 '  # 单个匹配
                           ]
        advisories_testcases = []
        generate_testcases(advisories_list, advisories_testcases, github_searcher.advisories_search_by_url)

    if __name__ == '__main__':
        unittest.main()
