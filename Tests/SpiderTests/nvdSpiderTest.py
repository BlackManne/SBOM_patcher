import unittest

# from Utils.CryptoUtils import TokenEncryptor
from spider.nvd_spider import nvd_crawl_by_time
from datetime import datetime, timedelta


class TestNVDSpider(unittest.TestCase):

    def test_nvd_crawl_by_time(self):
        # 获取当前日期
        current_date = datetime.now()
        # 计算昨天的日期
        yesterday = current_date - timedelta(days=1)

        # 格式化昨天的日期为字符串
        yesterday_str = yesterday.strftime('%Y-%m-%d')

        nvd_crawl_by_time(start_time=yesterday_str)

    if __name__ == '__main__':
        unittest.main()
