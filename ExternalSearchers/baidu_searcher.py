import re

import requests
from bs4 import BeautifulSoup

from Utils.util import get_page_content


class BaiduSearcher:
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/59.0.3071.115 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
            "Host": "www.baidu.com"
        }
        self.top_10_links = []

    def __get_real_url(self, v_url):
        """
        获取百度链接真实地址
        :param v_url: 百度链接地址
        :return: 真实地址
        """
        r = requests.get(v_url, headers=self.headers, allow_redirects=False)  # 不允许重定向
        if r.status_code == 302:  # 如果返回302，就从响应头获取真实地址
            real_url = r.headers.get('Location')
        else:  # 否则从返回内容中用正则表达式提取出来真实地址
            real_url = re.findall("URL='(.*?)'", r.text)[0]
        return real_url

    def __get_top_10_links(self, CVEid):
        for i in range(10):
            baidu_html = get_page_content(
                url=f'https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&wd={CVEid}&fenlei=256&oq'
                    f'=python&rsv_pq=8133476900ce391e&rsv_t=30efirUI%2BKNLZKOQJFwho4ugZmq8HSQSsQ9'
                    f'%2FVXI11Zx3VzRsuJQARd3GGCc&rqlang=cn&rsv_dl=tb&rsv_enter=0&rsv_btype=t&rsv_n=2&rsv_sug3=2'
                    f'&rsv_sug2=0&prefixsug=%2526lt%253BV%2526gt%253B-202%2526lt%253B-%2526lt%253B6%2526lt%253B96&rsp'
                    f'=0&inputT=720&rsv_sug4=720&rsv_sug=1&pn={i * 10}'
                , session=self.session)
            # print(baidu_html)
            soup = BeautifulSoup(baidu_html, 'html.parser')
            # 查找所有特定的<h3>标签
            h3_tags = soup.find_all('h3', class_='c-title t t tts-title')

            # 遍历每个<h3>标签
            for h3 in h3_tags:
                # 在每个<h3>标签内查找<a>标签
                a_tag = h3.find('a', href=True)
                # 如果找到了<a>标签，打印链接
                if a_tag:
                    print("fake url:", a_tag['href'])
                    real_url = self.__get_real_url(a_tag['href'])
                    print("real url:", real_url)
                    self.top_10_links.append(real_url)
                    if len(self.top_10_links) == 10:
                        return

    def search(self, CVEid):
        # print(baidu_html)
        self.__get_top_10_links(CVEid)


baidu_searcher = BaiduSearcher()
baidu_searcher.search('CVE-2023-36396')
