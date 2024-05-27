import time

import bs4
from lxml import etree

from RefPageParsers import apache_parser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

APACHE_CASE_URL = 'https://lists.apache.org/thread/04y4vrw1t2xl030gswtctc4nt1w90cb0'

if __name__ == '__main__':
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(APACHE_CASE_URL)
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CLASS_NAME, 'chatty_body'))
    )
    with open('../../Docs/ApacheCase.html', 'w') as f:
        f.write(driver.page_source)
    # soup = bs4.BeautifulSoup(driver.page_source, "lxml")
    # description_text = soup.find(class_='chatty_body')
    # print(description_text)
