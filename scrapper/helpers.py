import base64
import logging
import os.path
import time
from contextlib import contextmanager

from selenium import webdriver
from selenium.common import SessionNotCreatedException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from scrapper.constants import PROXY_ADDRESS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)


@contextmanager
def proxy_chrome_driver(proxy_address: str):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f'--proxy-server={proxy_address}')
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        yield driver
        driver.quit()
    except SessionNotCreatedException:
        msg = 'Chrome executor was not found.'
        logger.exception(msg)
        raise


@contextmanager
def quit_to_main_folder_context(driver: webdriver.Chrome):
    yield
    time.sleep(2)
    driver.execute_script("window.history.go(-2)")
    time.sleep(2)


def process_onion_link(tor_link: str) -> dict:
    with proxy_chrome_driver(PROXY_ADDRESS) as driver:
        logger.info('Start processing onion link...')

        driver.get(tor_link)
        output_json = {}
        try:
            page_table = WebDriverWait(driver, 10.0).until(
                expected_conditions.presence_of_element_located((By.XPATH, '//table[@id="list"]'))
            )
        except TimeoutException:
            logger.exception('Cannot find list table element. Try to restart...')
            raise

        table_rows = page_table.find_elements(By.XPATH, 'tbody/tr')
        for row in table_rows:
            link_element = row.find_element(By.XPATH, 'td[@class="link"]/a')
            title = link_element.get_attribute('title')
            link_element.click()
            time.sleep(2)

            with quit_to_main_folder_context(driver):
                link = driver.find_element(By.XPATH, '//table[@id="list"]//tr[2]//td[1]/a')
                title_child = link.get_attribute('title')
                extension = os.path.splitext(title_child)[1]
                link.click()

                file_content = driver.find_element(By.TAG_NAME, 'pre').text
                encoded_file_content = base64.b64encode(file_content.encode()).decode()
                output_json[title] = {
                    'title': title_child,
                    'file_extension': extension,
                    'file_content': encoded_file_content,
                }

    logger.info('Successfully processed onion link.')
    return output_json
