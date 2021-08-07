import os
import time

import pyperclip
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from stem import Signal
from stem.control import Controller

from src.models.tracking_number import TrackingNumber


class TooManyRequest(Exception):
    pass


class TooMuchTrackingNumbers(Exception):
    pass


class Crawl17Track:
    def __init__(self):
        self.tor_host = os.getenv('TOR_HOST') or '127.0.0.1'
        self.tor_port = int(os.getenv('TOR_PORT')) or 9050
        self.tor_password = os.getenv('TOR_PASSWORD')
        self.tor_controller_port = (
            int(os.getenv('TOR_CONTROLLER_PORT')) or 9051
        )
        self.driver_url = os.getenv('DRIVER_URL')
        self.driver = None
        self.init_driver()

    def init_driver(self, restart=False):
        if self.driver and restart:
            self.driver.quit()

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument(
            f'--proxy-server=socks5://{self.tor_host}:{self.tor_port}'
        )
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        )

        self.driver = webdriver.Chrome(self.driver_url, options=options)

    def terminate_driver(self):
        self.driver.close()

    def get_all_trackings(self, tracking_numbers=None):
        total_time = 0
        tracking_results = []
        for tracking_batch in self.__chunks(tracking_numbers, 40):
            for i in range(10):
                try:
                    start_time = time.time()
                    tracking_batch_result = self.get_tracking_by_batch(
                        tracking_batch
                    )
                    tracking_results += tracking_batch_result
                    end_time = time.time()
                    total_time += end_time - start_time
                    print(
                        f'DONE: {len(tracking_results)} / {len(tracking_numbers)}, took {end_time - start_time}s ( {total_time}s total )'  # noqa
                    )
                    print('Sleeping 5s..')
                    time.sleep(5)
                    break
                except Exception as e:
                    print(str(e))
                    print('Changing ip..')
                    time.sleep(i)
                    self.__switch_ip()
                    self.init_driver(restart=True)
                    continue
        return tracking_results

    def get_tracking_by_batch(self, tracking_numbers=None):
        tracking_numbers = tracking_numbers or []
        if len(tracking_numbers) > 40:
            raise TooMuchTrackingNumbers('Too much trackings in a batch')

        self.__normalize(tracking_numbers)
        self.__open_17track(tracking_numbers)
        # self.__close_intro_if_existed()
        # self.__check_request_limitation()
        self.__choose_carriers_if_ambiguous()

        return self.__get_tracking_details()

    def __open_17track(self, tracking_numbers):
        self.driver.get(
            'https://www.trackdog.com/track.html?tn=' + ','.join(tracking_numbers)
        )
        self.__wait_for_ajax_completed()

    def __close_intro_if_existed(self):
        intros = self.driver.find_elements_by_css_selector(
            '.introjs-skipbutton'
        )
        if intros:
            intros[0].click()

    def __check_request_limitation(self):
        try:
            request_is_limited = (
                'Your tracking is too frequent'
                in self.driver.find_element_by_css_selector(
                    '.yqcr-error-cell'
                ).text
            )
        except:
            request_is_limited = False

        if request_is_limited:
            raise TooManyRequest('Limited')

    def __choose_carriers_if_ambiguous(self):
        driver = self.driver
        for i in range(30):
            loading_cells = driver.find_elements_by_css_selector(
                '.yqcr-loading-cell'
            )

            if len(loading_cells) > 0:
                time.sleep(2)
                continue

            multi_carriers = driver.find_elements_by_css_selector(
                '.multi-carriers'
            )

            if len(multi_carriers) > 0:
                for multi_carrier in multi_carriers:
                    try:
                        multi_carrier.find_element_by_css_selector(
                            '[data-key]'
                        ).click()
                        time.sleep(0.1)
                    except:
                        continue
                continue

            break
        self.__wait_for_ajax_completed()

    def __get_tracking_details(self):
        driver = self.driver
        copy_all_button = driver.find_element_by_xpath(
            "//div[contains(@class, 'batch_operation_box')]//a[contains(@class, 'iconfuzhi')]"
        )
        copy_all_button.click()

        all_detail = pyperclip.paste()

        tracking_numbers = []
        for detail in all_detail.split('\n\n\n')[:-1]:
            tracking_number = TrackingNumber.create_from_17track_clipboard(
                detail
            )

            tracking_numbers.append(tracking_number)
            print(f'scanned {tracking_number.tracking_number}')

        return tracking_numbers

    def __switch_ip(self):
        with Controller.from_port(port=self.tor_controller_port) as controller:
            if self.tor_password:
                controller.authenticate(password=self.tor_password)
            else:
                controller.authenticate()
            controller.signal(Signal.NEWNYM)

    def __wait_for_ajax_completed(self):
        wait = WebDriverWait(self.driver, 30)
        try:
            wait.until(
                lambda driver: driver.execute_script('return jQuery.active')
                == 0
            )
            wait.until(
                lambda driver: driver.execute_script(
                    'return document.readyState'
                )
                == 'complete'
            )
        except Exception as e:
            pass
        self.driver.implicitly_wait(2)

    @staticmethod
    def __chunks(l, n):
        n = max(1, n)
        return (l[i : i + n] for i in range(0, len(l), n))

    @staticmethod
    def __normalize(tracking_numbers=None):
        tracking_numbers = [t.strip() for t in tracking_numbers if t.strip()]

        return tracking_numbers
