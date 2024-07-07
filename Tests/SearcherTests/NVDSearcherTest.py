import unittest
from ExternalSearchers import nvd_searcher
from Tests.Utils.test_utils import generate_testcases


class TestNVDSearcher(unittest.TestCase):

    def test_nvd_search(self):
        nvd_list = ['https://nvd.nist.gov/vuln/detail/CVE-2022-1',  # 无效的
                    'https://nvd.nist.gov/vuln/detail/CVE-2022-28066',  # 被拒绝的
                    'https://nvd.nist.gov/vuln/detail/CVE-2023-43746',  # 没有patch
                    'https://nvd.nist.gov/vuln/detail/CVE-2023-36569',  # 微软的patch
                    'https://nvd.nist.gov/vuln/detail/CVE-2023-37582',  # github的patch
                    'https://nvd.nist.gov/vuln/detail/CVE-2020-19952',
                    'https://nvd.nist.gov/vuln/detail/CVE-2023-36568'
                    ]
        generate_testcases(nvd_list, nvd_searcher.search_nvd_using_url)

    if __name__ == '__main__':
        unittest.main()
