import os
from time import sleep
import requests
import hashlib
import io
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import matplotlib
import torch
import tkinter as tk
from PIL import ImageTk, Image
from torchvision import transforms

from utility import Driver, By, TimeoutException
from property import Property

# SECTION globals
DISPLAY_SIZE = 672


# SECTION functions - utility
def open_driver(**kwargs):
    """
    Opens a Driver instance, goes to funda.nl and denies the cookies
    :param kwargs:
    :return:
    """
    monitor = 1
    if 'monitor' in kwargs:
        monitor = kwargs.pop('monitor')

    driver = Driver(monitor=monitor, **kwargs)
    driver.get('https://www.funda.nl')

    driver.wait_for((By.XPATH, '//button[@id="didomi-notice-disagree-button"]'), click=True, wait_seconds=30)
    # driver.execute_cdp_cmd('Network.enable', {})
    # driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': IMAGE_BLOCK_PATTERNS})
    return driver


def get_urls_current_page(driver):
    make_url = lambda listing_id: f'https://www.funda.nl/detail/{listing_id}'
    elements = driver.find_elements(By.XPATH, '//h2/a[@href]')
    ids = [e.get_attribute('href').split('/')[-2] for e in elements]
    return [make_url(l_id) for l_id in ids]



# SECTION scraping


if __name__ == '__main__':
    driver = open_driver()
    driver.get('https://www.funda.nl/zoeken/koop')
    listing_urls = get_urls_current_page(driver)
    for listing_url in listing_urls:
        property = Property.from_listing_id(driver, listing_url)
        property.to_csv()


