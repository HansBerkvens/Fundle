from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import selenium.common.exceptions as exceptions
from typing import Iterable
from time import sleep
from contextlib import suppress
import subprocess
import re
import sys


class Driver(uc.Chrome):
    def __init__(self, monitor: int = 0, monitor_size: int = 3000, block_images: bool = False, **kwargs):
        """
        Open undetected chromedriver in fullscreen on the specified monitor (-1 = left, 0 = main, 1 = right)
        """
        if 'version_main' not in kwargs:
            kwargs['version_main'] = Driver._get_chrome_major_version()

        if block_images:
            options = kwargs.pop('options', uc.ChromeOptions())
            options.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})
            kwargs['options'] = options

        super().__init__(**kwargs)

        # allow some time to fully initialize object
        sleep(1)

        # move driver window to desired monitor (negative = left, positive = right)
        self.set_window_position(x=monitor * monitor_size, y=0)

        # maximize window
        self.maximize_window()

    @staticmethod
    def _get_chrome_major_version() -> int | None:
        """Auto-detect the installed Chrome major version across platforms."""
        cmds = {
            'win32': [
                r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version',
                r'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon" /v version',
            ],
            'darwin': [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version',
            ],
        }
        linux_cmd = 'google-chrome --version || chromium-browser --version || chromium --version'

        try:
            if sys.platform == 'win32':
                for cmd in cmds['win32']:
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
                    if match:
                        return int(match.group(1))

            elif sys.platform == 'darwin':
                for cmd in cmds['darwin']:
                    result = subprocess.run(cmd.split(), capture_output=True, text=True)
                    match = re.search(r'(\d+)\.\d+\.\d+', result.stdout)
                    if match:
                        return int(match.group(1))

            else:  # Linux
                result = subprocess.run(linux_cmd, capture_output=True, text=True, shell=True)
                match = re.search(r'(\d+)\.\d+\.\d+', result.stdout)
                if match:
                    return int(match.group(1))

        except Exception as e:
            print(f"[Driver] Could not detect Chrome version: {e}")

        print("[Driver] Falling back to version_main=None (uc will attempt auto-match)")
        return None

    def click_element(self, element: Iterable | str, optional_element: str | None = None) -> bool:
        """
        Given an element as Iterable of two strings, or element and optional_element as two strings
        Find the webelement in the driver and click it.
        If the first click fails, scroll down and try again, then scroll up and try again.
        Lastly, try to scroll element into view and try again.
        """
        if isinstance(element, Iterable):
            wait_by, wait_el = element
        else:
            wait_by = str(element)
            wait_el = str(optional_element)

        x = (wait_by, wait_el)

        webelement: WebElement = self.find_element(*x)

        with suppress(Exception):
            webelement.click()
            return True

        for script in ["arguments[0].scrollIntoView();",
                       'window.scrollBy(0, 200);',  # scroll down
                       'window.scrollBy(0, -300);',  # scroll up
                       ]:
            with suppress(Exception):
                self.execute_script(script, webelement)
                return True

        return False

    def wait_for(self, element: Iterable | str, optional_element: str | None = None, click: bool = False,
                 wait_seconds: float = 10.) -> WebElement | None:
        """
        Given an element as Iterable of two strings, or element and optional_element as two strings
        Wait for the element to be present or clickable.
        If click was passed as True, it will also click the element.
        It will wait for a maximum of wait_seconds for the element to appear.

        Returns:
            (WebElement | None): The webelement that was waited for, or None if the element was clicked
        """
        if isinstance(element, Iterable):
            wait_by, wait_el = element
        else:
            wait_by = str(element)
            wait_el = str(optional_element)

        x = (wait_by, wait_el)

        if click:
            element_present = EC.element_to_be_clickable(x)
        else:
            element_present = EC.presence_of_element_located(x)

        WebDriverWait(self, wait_seconds).until(element_present)

        if click:
            self.click_element(x)
        else:
            return self.find_element(*x)


if __name__ == '__main__':
    driver = Driver()
    driver.get('https://www.funda.nl/detail/koop/amsterdam/appartement-rietwijkerstraat-39-1/89695189/overzicht/')
    rndm_img_elmnt = driver.find_element(By.XPATH, '//a[contains(@href, "media/foto/37")]')
    # driver.execute_script("arguments[0].scrollIntoView();", rndm_img_elmnt)
