import time
import json

from http.client import RemoteDisconnected

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from stem import Signal
from stem.control import Controller

from models.tracking_number import TrackingNumber

DRIVER_URL = '/home/upinus/17track-crawler/chromedriver_linux'
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
options.add_argument(
    '--user-agent=5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.3497.100 Safari/537.36'
)



driver = webdriver.Chrome(DRIVER_URL, options=options)
f = open("result.txt", "w")
tf = open("tracking_number.txt", "r")


class TooManyRequest(Exception):
    pass


def get_proxies():
    driver.get("https://sslproxies.org/")
    driver.execute_script(
        "return arguments[0].scrollIntoView(true);",
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located(
                (
                    By.XPATH,
                    "//table[@class='table table-striped table-bordered dataTable']//th[contains(., 'IP Address')]",
                )
            )
        ),
    )
    ips = [
        my_elem.get_attribute("innerHTML")
        for my_elem in WebDriverWait(driver, 5).until(
            EC.visibility_of_all_elements_located(
                (
                    By.XPATH,
                    "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 1]",
                )
            )
        )
    ]
    ports = [
        my_elem.get_attribute("innerHTML")
        for my_elem in WebDriverWait(driver, 5).until(
            EC.visibility_of_all_elements_located(
                (
                    By.XPATH,
                    "//table[@class='table table-striped table-bordered dataTable']//tbody//tr[@role='row']/td[position() = 2]",
                )
            )
        )
    ]
    proxies = []
    for i in range(0, len(ips)):
        proxies.append(ips[i] + ':' + ports[i])

    return proxies


# signal TOR for a new connection
def switch_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='upinus2017')
        controller.signal(Signal.NEWNYM)


def wait_for_ajax(driver):
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(
            lambda driver: driver.execute_script('return jQuery.active') == 0
        )
        wait.until(
            lambda driver: driver.execute_script('return document.readyState')
            == 'complete'
        )
    except Exception as e:
        pass


def chunks(l, n):
    n = max(1, n)
    return (l[i : i + n] for i in range(0, len(l), n))


def get_tracking_info(tracking_numbers=None):
    tracking_numbers = tracking_numbers or []
    driver.get('https://t.17track.net/en#nums=' + ','.join(tracking_numbers))
    wait_for_ajax(driver)
    intros = driver.find_elements_by_css_selector('.introjs-skipbutton')

    if intros:
        intros[0].click()

    try:
        request_is_limited = (
            'Your tracking is too frequent'
            in driver.find_element_by_css_selector('.yqcr-error-cell').text
        )
    except:
        request_is_limited = False

    if request_is_limited:
        raise TooManyRequest('Limited')

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

    wait_for_ajax(driver)
    detail_buttons = driver.find_elements_by_css_selector(
        'button[data-copy-details]'
    )

    if len(detail_buttons) == 0:
        raise Exception('Can not find any result')

    for detail_button in detail_buttons:
        detail = detail_button.get_attribute('data-clipboard-text')
        tracking_number = TrackingNumber.create_from_17track_clipboard(detail)

        tracking_number_json = json.dumps(tracking_number.to_dict())
        print(f'scanned {tracking_number.tracking_number}')
        f.write(tracking_number_json + '\n')


tracking_numbers = tf.readlines()

done_tracking = 0
total_time = 0
for tracking_batch in chunks(tracking_numbers, 40):
    for i in range(10):
        try:
            start_time = time.time()
            get_tracking_info(tracking_batch)
            end_time = time.time()
            time.sleep(5)
            done_tracking += len(tracking_batch)
            total_time += end_time - start_time
            print(
                f'DONE: {done_tracking} / {len(tracking_numbers)}, took {end_time - start_time}s ( {total_time}s total )'
            )
            break
        except Exception as e:
            print(str(e))
            print('Changing ip..')
            time.sleep(i)
            switch_ip()
            driver.quit()
            driver = webdriver.Chrome(DRIVER_URL, options=options)
            continue

driver.close()
f.close()
tf.close()
