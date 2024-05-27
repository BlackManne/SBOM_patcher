from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

from Utils import util
import RefPageParsers.github_parser


def get_apache_html(link):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(link)
    # 等待js动态加载出描述后再返回页面内容
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CLASS_NAME, 'chatty_body'))
    )
    return driver.page_source


def parse(url):
    # 正常代码
    # apache_page_html = get_apache_html(url)
    # soup = BeautifulSoup(apache_page_html, "lxml")
    # 测试用
    soup = BeautifulSoup(open('../Docs/ApacheCase.html'), 'lxml')

    # 提取纯文本描述
    # description_text = soup.find(class_='chatty_body')
    description_text = soup.find(class_='chatty_body').span.get_text()

    print(description_text)

    # 从描述文本中获取url并去重
    urls = util.get_URL_from_text(str(description_text))
    print(urls)

    # 寻找github链接进行跳转，交由github parser进行处理
    for url in urls:
        if "github" in url:
            print(url)
            # todo:等待github parser支持pull页面
            # github_parser.github_parse(url)


if __name__ == '__main__':
    parse("test")
