import unittest
from RefPageParsers import github_parser


class TestGithubParser(unittest.TestCase):

    def test_commit_parse(self):
        pass

    def test_advisory_parse(self):
        url_list = [
            "https://github.com/advisories/GHSA-6qjm-h442-97p9",
            "https://github.com/advisories/GHSA-fxg5-wq6x-vr4w",
            "https://github.com/kyverno/kyverno/security/advisories/GHSA-9g37-h7p2-2c6r",
            "https://github.com/actions/toolkit/security/advisories/GHSA-7r3h-m5j6-3q42",  # todo 第五个的reference解析还是有问题
            "https://github.com/fastify/github-action-merge-dependabot/security/advisories/GHSA-v5vr-h3xq-8v6w",
            "https://github.com/git/git/security/advisories/GHSA-j342-m5hw-rr3v",
            "https://github.com/github/gh-ost/security/advisories/GHSA-rrp4-2xx3-mv29",
            "https://github.com/cloudflare/cfrpki/security/advisories/GHSA-3pqh-p72c-fj85"]
        for url in url_list:
            github_parser.advisory_parse(url)

    def test_issue_parse(self):
        pass

    def test_pull_parse(self):
        pass

    def test_github_parser(self):
        url_list = [
            "https://github.com/advisories/GHSA-6qjm-h442-97p9",
            "https://github.com/kyverno/kyverno/security/advisories/GHSA-9g37-h7p2-2c6r",
            ]
        for url in url_list:
            github_parser.github_parse(url)

    if __name__ == '__main__':
        unittest.main()