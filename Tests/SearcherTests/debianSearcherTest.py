import unittest

from ExternalSearchers import debian_searcher
from Tests.Utils.test_utils import generate_testcase_general


class TestDebianSearcher(unittest.TestCase):

    def test_debian_search(self):
        debian_list = ['CVE-2021-36489',
                    'CVE-2024-21490',
                    'CVE-2024-29857',
                    'CVE-2024-2199',
                    'CVE-2024-31459',
                    'CVE-2023-50868',
                    'CVE-2023-38545',
                    'CVE-2023-28686',
                    'CVE-2023-50867'
                    ]
        prefix = 'https://security-tracker.debian.org/tracker/'
        generate_testcase_general([prefix + item for item in debian_list], debian_list,
                                  debian_searcher.debian_search_by_cve_id)

    if __name__ == '__main__':
        unittest.main()