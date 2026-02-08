from abc import abstractmethod
import os
import requests
from typing import Callable
from .. import common
from .. import log
from . import inputSource

class HtmlInputSource(inputSource.InputSource):
    def __init__(self, count: int):
        self.headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.count = count

    @abstractmethod
    def get_new_images(self, input_source: str) -> int: 
        ...

    @abstractmethod
    def get_image_url(self, html: str) -> str | None:
        ...

    def read_html(self, url: str) -> str | None:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            html = response.text
            return html
        except requests.exceptions.RequestException as e:
            log.error(f"Error reading {url}: {e}")
            return None

    def download_image(self, url, input_source: str) -> bool:
        """
        Downloads an image from a URL and saves it to a specified directory.
        
        Args:
            url (str): The URL of the image to download.
        """
        try:
            # Get the filename from the URL
            filename = os.path.basename(url.split("?")[0])

            # Construct the full path to save the file
            save_path = os.path.join(f"{common.INPUT_SOURCES_IN}/{input_source}", filename)

            # Define a User-Agent header to mimic a web browser

            # Send a GET request with the headers
            response = requests.get(url, headers=self.headers, timeout=10)        
            # Check if the request was successful
            if response.status_code == 200:
                # Open the file in binary write mode and write the content
                with open(save_path, "wb") as file:
                    file.write(response.content)
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            log.error(f"An error occurred during the download: {e}")
        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")

        return False

    def process_url(self, url: str, input_source: str) -> bool:
        html = self.read_html(url)
        if html:
            img_url = self.get_image_url(html)
            if img_url:
                if "svg" in img_url:
                    return log.error(f"svg: {input_source}") 
                if self.download_image(img_url, input_source):                    
                    return True

        return log.error(f"Unable to read html for {input_source}") 

    def fetch(self, get_url: Callable[[int], str], input_source: str, min_year: int, file_count: int) -> int:
        max_fails: int = file_count // 2
        fetch_count: int = 0
        fails: int = 0

        while fetch_count < file_count and fails <= max_fails:
            url: str = get_url(min_year)
            if self.process_url(url, input_source):
                fetch_count += 1
                continue
            fails += 1
            log.error(f"{fails=}: Unable to fetch {url}")
        return fetch_count 
