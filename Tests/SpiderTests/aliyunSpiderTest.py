import unittest

from spider import AliCloud_spider
from datetime import datetime, timedelta


class TestAliyunSpider(unittest.TestCase):

    def test_aliyun_crawl_by_time(self):
        # 获取当前日期
        current_date = datetime.now()
        # 计算昨天的日期
        yesterday = current_date - timedelta(days=1)

        # 格式化昨天的日期为字符串
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        print(yesterday_str)

        AliCloud_spider.alicloud_crawl_by_time(start_time=yesterday_str)

    if __name__ == '__main__':
        unittest.main()
