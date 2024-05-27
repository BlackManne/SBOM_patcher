from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By


class WindowsParser:
    def __init__(self):
        # self.driver = webdriver.Edge('.\\msedgedriver.exe')
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')
        # 设置页面加载策略
        # chrome_options.page_load_strategy = 'normal'  # 或 'none', 'eager'
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait_one = WebDriverWait(self.driver, 1)
        self.wait_three = WebDriverWait(self.driver, 3)
        self.wait_five = WebDriverWait(self.driver, 5)
        # self.session = requests.session()

    def __parse_basic_score_index(self):
        basic_score_index = {}
        for i in range(1, 9):
            index_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[1]/div/div/div[4]/div['
                                                             f'3]/div/div/div[2]/div/div/div/div/div[1]/div/div/div['
                                                             f'2]/div/div/div[{i}]/div/div/div[1]/details/summary')
            )
            index = index_element.text
            value_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[1]/div/div/div[4]/div['
                                                             f'3]/div/div/div[2]/div/div/div/div/div[1]/div/div/div['
                                                             f'2]/div/div/div[{i}]/div/div/div[2]/details/summary')
            )
            value = value_element.text
            basic_score_index[index] = value
        print(basic_score_index)

    def __parse_time_score_index(self):
        time_score_index = {}
        for i in range(1, 4):
            index_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[1]/div/div/div[4]/div['
                                                             f'3]/div/div/div[2]/div/div/div/div/div[2]/div/div/div['
                                                             f'2]/div/div/div[{i}]/div/div/div[1]/details/summary')
            )
            index = index_element.text
            value_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[1]/div/div/div[4]/div['
                                                             f'3]/div/div/div[2]/div/div/div/div/div[2]/div/div/div['
                                                             f'2]/div/div/div[{i}]/div/div/div[2]/details/summary')
            )
            value = value_element.text
            time_score_index[index] = value
        print(time_score_index)

    def __parse_usage(self):
        usage = {}
        for i in range(1, 4):
            index_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[2]/div/div['
                                                             f'2]/div/div/div/div/div[1]/div/div[{2 * i - 1}]/span/span/span')
            )
            index = index_element.text
            value_element = self.wait_five.until(
                lambda driver: driver.find_element(By.XPATH, f'/html/body/div[1]/div/div/div/div/div/div/div/div['
                                                             f'2]/div/div/div[2]/div[3]/div[2]/div/div['
                                                             f'2]/div/div/div/div/div['
                                                             f'2]/div/div/div/div/div/div/div/div[{i}]')
            )
            value = value_element.text
            usage[index] = value
        print(usage)

    def parse(self, url):
        self.driver.get(url)
        # 获取 基本分数指标
        self.__parse_basic_score_index()
        # 获取 时间得分指标
        self.__parse_time_score_index()
        # 获取 可利用性
        self.__parse_usage()


# 单例模式 实例化
win_parser = WindowsParser()
# win_parser.parse('https://msrc.microsoft.com/update-guide/vulnerability/CVE-2023-36427')
