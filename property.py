import re
import io
import os
import requests
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

from torchvision import transforms
import pandas as pd
from PIL import ImageTk, Image
import torch

from utility import Driver, By
from nn_classifier import predict_labels
from image import TensorImage


def create_tensors(listing_id, image_urls) -> list[TensorImage]:
    def make_one(image_url):
        return TensorImage(listing_id, image_url)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_one, url) for url in image_urls]
    return [f.result() for f in futures]


def find_image_urls_from_listing(driver: Driver, url: str):
    """given a listing url, retrieve the image_url for all advertisement images"""
    driver.get(url)
    driver.wait_for((By.XPATH, '//a[@href="https://www.funda.nl"]'), wait_seconds=5)


    driver.get(f'{driver.current_url}/overzicht')
    driver.wait_for((By.XPATH, '//a[contains(@href, "media/foto")]'), wait_seconds=4)

    result = driver.execute_script("""
            const anchors = document.querySelectorAll('a[href*="media/foto"]');
            const results = [];
            for (let i = 0; i < anchors.length; i++) {
                const img = anchors[i].querySelector('img');
                if (img) results.push(img.src);
            }
            return results;
        """)

    driver.get('about:blank')
    return result


def find_property_information_from_listing_url(driver: Driver, url: str):
    driver.get(url)
    price_str = driver.find_element(By.XPATH, '//span[contains(text(), "€")]').text
    price = int(re.sub(r'[^\d]', '', re.search(r'€[\d.\s]+', price_str).group()))

    size_str = driver.find_element(By.XPATH,'//div[contains(@id, "category-afmetingen")]//dt[contains(normalize-space(.), "Wonen")]/following-sibling::dd[1]').text
    size = int(re.sub(r'\D', '', re.search(r'\d+', size_str).group()))

    rooms = driver.find_element(By.XPATH,'//div[contains(@id, "category-indeling")]//dt[contains(normalize-space(.), "Aantal kamers")]/following-sibling::dd[1]').text

    energy_label = driver.find_element(By.XPATH,'//div[contains(@id, "category-energie")]//dt[contains(normalize-space(.), "Energielabel")]/following-sibling::dd[1]').text

    location = driver.find_element(By.XPATH, '//div[@id="about"]/div[2]/div/div/h1/span[2]').text

    return price, size, rooms, energy_label, location


@dataclass
class Property:
    listing_id: str
    price: int
    size: int
    rooms: str
    energy_label: str
    location: str
    images: list[TensorImage]

    @classmethod
    def from_listing_id(cls, driver: Driver, listing_url: str):
        if listing_url.endswith('/'):
            listing_url = listing_url[:-1]
        listing_id = listing_url.split('/')[-1]
        price, size, rooms, energy_label, location = find_property_information_from_listing_url(driver, listing_url)

        image_urls = find_image_urls_from_listing(driver, listing_url)
        tensors: list[TensorImage] = create_tensors(listing_id, image_urls)

        return cls(
            listing_id=listing_id,
            price=price,
            size=size,
            rooms=rooms,
            energy_label=energy_label,
            location=location,
            images=tensors,
        )

    def to_csv(self):
        pd.DataFrame({
            'listing_id': self.listing_id,
            'price': self.price,
            'size': self.size,
            'rooms': self.rooms,
            'energy_label': self.energy_label,
            'location': self.location,
            'image_url': [t.image_url for t in self.images],
            'hash': [t.hash for t in self.images],
            'class_prediction': [t.class_prediction for t in self.images],
            'confidence': [t.confidence for t in self.images],
        }).to_csv('properties.csv', index=False, header=False, mode='a')





