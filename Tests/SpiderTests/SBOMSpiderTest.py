import unittest

from datetime import datetime, timedelta

import time

import SBOM


class TestSBOMSpider(unittest.TestCase):

    def test_SBOM_crawl_by_time(self):
        # 获取当前日期
        current_date = datetime.now()
        # 计算昨天的日期
        yesterday = current_date - timedelta(days=1)

        # 格式化昨天的日期为字符串
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        print(yesterday_str)

        exec_start_time = time.time()

        SBOM.crawl_by_time(start_time=yesterday_str)

        exec_end_time = time.time()

        execution_time = exec_end_time - exec_start_time
        print(f"增量爬取一天内的数据的执行时间：{execution_time} 秒")

    if __name__ == '__main__':
        unittest.main()
