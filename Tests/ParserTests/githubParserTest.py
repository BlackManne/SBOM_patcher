import unittest
from RefPageParsers import github_parser
from Tests.Utils.test_utils import generate_testcases


class TestGithubParser(unittest.TestCase):

    def test_commit_parse(self):
        url_list = [
            "https://github.com/PX4/PX4-Autopilot/commit/d1fcd39a44e6312582c6ab02b0d5ee2599fb55aa",
        ]
        generate_testcases(url_list, github_parser.commit_parse)

    def test_advisory_parse(self):
        url_list = [
            "https://github.com/advisories/GHSA-6qjm-h442-97p9",
            "https://github.com/advisories/GHSA-fxg5-wq6x-vr4w",
            "https://github.com/kyverno/kyverno/security/advisories/GHSA-9g37-h7p2-2c6r",
            "https://github.com/actions/toolkit/security/advisories/GHSA-7r3h-m5j6-3q42",
            "https://github.com/fastify/github-action-merge-dependabot/security/advisories/GHSA-v5vr-h3xq-8v6w",
            "https://github.com/git/git/security/advisories/GHSA-j342-m5hw-rr3v",
            "https://github.com/github/gh-ost/security/advisories/GHSA-rrp4-2xx3-mv29",
            "https://github.com/cloudflare/cfrpki/security/advisories/GHSA-3pqh-p72c-fj85"]
        generate_testcases(url_list, github_parser.advisory_parse)

    def test_issue_parse(self):
        url_list = [
            "https://github.com/Lissy93/dashy/issues/1336",
            "https://github.com/jbt/markdown-editor/issues/106",
            "https://github.com/go-sonic/sonic/issues/56"
        ]
        generate_testcases(url_list, github_parser.issue_parse)

    def test_pull_parse(self):
        url_list = [
            "https://github.com/openshift/kubernetes/pull/1736",
            "https://github.com/PX4/PX4-Autopilot/pull/17264/commits/555f900cf52c0057e4c429ff3699c91911a21cab",
        ]
        generate_testcases(url_list, github_parser.pull_parse)

    def test_github_parser(self):
        url_list = [
            "https://github.com/PX4/PX4-Autopilot/commit/d1fcd39a44e6312582c6ab02b0d5ee2599fb55aa",
            "https://github.com/advisories/GHSA-6qjm-h442-97p9",
            "https://github.com/kyverno/kyverno/security/advisories/GHSA-9g37-h7p2-2c6r",
            "https://github.com/Lissy93/dashy/issues/1336",
            "https://github.com/openshift/kubernetes/pull/1736"
            ]
        generate_testcases(url_list, github_parser.github_parse)

    if __name__ == '__main__':
        unittest.main()