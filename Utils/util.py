import requests
from random import randint
from urlextract import URLExtract


def github_url_transfer(url):
    # 把每一个github url转换为调用api.github.com的链接
    return str(url).replace("github.com", "api.github.com/repos")


def get_page_content(url, session=None):
    user_agent = [
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.7113.93 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
    ]
    try:
        if session is None:
            response = requests.get(url, headers={'User-Agent': user_agent[randint(0, 1)]})
        else:
            response = session.get(url, headers={'User-Agent': user_agent[randint(0, 1)]})
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return response.text
        return
    except Exception:
        return


def get_URL_from_text(text):
    urlExtractor = URLExtract()
    return list(set(urlExtractor.find_urls(text)))
