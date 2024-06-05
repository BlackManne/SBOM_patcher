import unittest
from ExternalSearchers import nvd_searcher


class TestNVDSearcher(unittest.TestCase):

    def test_different_page_search(self):
        nvd_list = ['CVE-2022-1',  # 无效的
                    'CVE-2022-28066',  # 被拒绝的
                    'CVE-2020-19952',  # github的patch
                    'CVE-2023-43746',  # 没有patch
                    'CVE-2023-36569'  # 微软的patch
                    ]
        for nvd_url in nvd_list:
            nvd_searcher.parse_nvd(nvd_url)

    def test_software_version_parse(self):
        nvd_list = ['CVE-2023-37582',
                    'CVE-2020-19952',
                    'CVE-2023-43746',
                    'CVE-2023-36568'
                    ]
        for cve_id in nvd_list:
            nvd_searcher.search_nvd(cve_id)

    if __name__ == '__main__':
        unittest.main()
