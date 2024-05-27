from Utils import util
from bs4 import BeautifulSoup


def parse(url):
    # todo:parse apple webpage
    # apple爬虫限制最多每秒5次，
    # Disallow: /kb/index?*page=search*
    # Disallow: *src=support_app*
    # 可以直接抓取，不需要等待动态加载
    apple_page_html = util.get_page_content(url)
    soup = BeautifulSoup(apple_page_html, 'lxml')
    description_text = soup.find(id="content").div.get_text()
    print(description_text)


if __name__ == '__main__':
    parse('https://support.apple.com/zh-cn/103447')
