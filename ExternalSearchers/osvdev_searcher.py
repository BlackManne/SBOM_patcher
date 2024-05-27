import requests

from RefPageParsers import github_parser


class OSVdevSearcher:
    def __init__(self):
        # OSV.dev API端点
        self.api_endpoint = "https://api.osv.dev/v1/query"
        self.api_endpoint_cve_base = "https://api.osv.dev/v1/vulns/"
        # 通过通过软件包版本查询 或者 通过提交哈希查询
        self.query_method = 1

    def __set_query_method(self, method):
        self.query_method = method

    def __query_by_version(self):
        """查询指定版本的软件包漏洞"""
        package_name = input("请输入软件包名：")
        version = input("请输入版本：")
        ecosystem = input("请输入包所属生态系统：")
        payload = {
            "version": version,
            "package": {
                "name": package_name,
                "ecosystem": ecosystem
            }
        }
        response = requests.post(self.api_endpoint, json=payload)
        return response

    def __query_by_commit(self):
        """查询指定提交哈希的漏洞"""
        commit_hash = input("请输入提交哈希值：")
        payload = {"commit": commit_hash}
        response = requests.post(self.api_endpoint, json=payload)
        return response

    # 对外接口1：通过包查相关漏洞
    def search_from_software(self):
        print("您希望通过软件包版本查询（输入1）还是通过提交哈希查询（输入2）？")
        self.__set_query_method(int(input()))
        if self.query_method == 1:
            print("将通过软件包版本查询。")
            response = self.__query_by_version()
        else:
            print("将通过哈希值查询。")
            response = self.__query_by_commit()
        if response.status_code == 200:
            print("Vulnerabilities for package version:", response.json())
        else:
            print("Failed to fetch data for package version:", response.status_code)

    def __query_vulnerability(self, CVE_id):
        """查询漏洞详情，包括相关补丁信息"""
        response = requests.get(self.api_endpoint_cve_base + CVE_id)
        # 示例：查询漏洞并获取补丁信息
        if response.status_code == 200:
            vuln_data = response.json()
            print("Vulnerability details:", vuln_data)
            # 提取ADVISORY，FIX，REPORT，WEB等信息
            if "references" in vuln_data:
                for reference in vuln_data["references"]:
                    print(reference)
                    if reference['type'] == 'ADVISORY' or reference['type'] == 'FIX':
                        print(reference['url'])
                        print(github_parser.github_parse(reference['url']))
        else:
            print("Failed to fetch data for vulnerability:", response.status_code)

    # 对外接口2：通过漏洞编号搜索漏洞信息
    def search_CVE(self, CVE_id):
        self.__query_vulnerability(CVE_id)


osddev_searcher = OSVdevSearcher()
osddev_searcher.search_from_software()
osddev_searcher.search_CVE("CVE-2022-27651")
