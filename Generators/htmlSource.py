from abc import abstractmethod
import os
import time
import requests
from typing import Callable

# Inherits from the newly refactored Source
from .source import Source

class HtmlSource(Source):
    """
    Utility class for scraping and downloading images from HTML pages.
    """
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    @abstractmethod
    def get_image_url(self, html: str) -> str | None:
        """Children (like Wiki) must implement this to parse the HTML."""
        pass

    def read_html(self, url: str) -> str | None:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() 
            return response.text
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error reading {url}: {e}")
            return None

    def download_image(self, url: str, input_source: str) -> bool:
        try:
            filename = os.path.basename(url.split("?")[0])
            out_dir = os.path.join(self.config["paths"]["generators_in"], input_source)
            os.makedirs(out_dir, exist_ok=True)
            
            save_path = os.path.join(out_dir, filename)

            response = requests.get(url, headers=self.headers, timeout=10)        
            if response.status_code == 200:
                self.log.debug(f"Download {url} - 200 OK")
                with open(save_path, "wb") as file:
                    file.write(response.content)
                return True
            else:
                self.log.warning(f"Download {url} - Status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log.error(f"An error occurred during the download: {e}")
        except Exception as e:
            self.log.error(f"An unexpected error occurred: {e}")
        return False

    def process_url(self, url: str, input_source: str) -> bool:
        html = self.read_html(url)
        if html:
            img_url = self.get_image_url(html)
            if img_url:
                if "svg" in img_url:
                    self.log.warning(f"Skipping SVG format for {input_source}") 
                    return False
                if self.download_image(img_url, input_source):                    
                    return True

        self.log.error(f"Unable to process or find image in HTML for {input_source}") 
        return False

    def fetch(self, get_url: Callable[[int], str], input_source: str, min_year: int, file_count: int) -> int:
        MAX_FAILS_IN_LOOP = 3
        TOTAL_FAILS_ALLOWED = 6
        total_fails = 0
        fetch_count = 0

        while fetch_count < file_count:
            url = get_url(min_year)
            fails = 0

            while fails < MAX_FAILS_IN_LOOP:
                self.log.info(f"{fetch_count+1}/{file_count},{fails=}")
                if self.process_url(url, input_source):
                    break
                fails += 1
                total_fails += 1
                time.sleep(3)

            if total_fails > TOTAL_FAILS_ALLOWED:
                self.log.error(f"Total fails: {total_fails} is greater than {TOTAL_FAILS_ALLOWED}")
                return fetch_count
            elif fails == MAX_FAILS_IN_LOOP:
                self.log.error(f"Failed {fails} times: Unable to fetch {url}")
            else:
                fetch_count += 1

        return fetch_count
