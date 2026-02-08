from abc import ABC, abstractmethod
from typing import Callable
from datetime import date, timedelta
import os
import random
import requests
from .. import common

class InputSource(ABC):
    def get_random_date(self, min_year: int) -> date:
        start_date = date(min_year, 1, 1)
        current_date = date.today()
        delta = current_date - start_date
        num_days = delta.days

        # Generate a random number of days within the range
        random_days = random.randint(0, num_days)

        # Add the random number of days to the start date to get a random date
        random_date = start_date + timedelta(days=random_days)

        return random_date

    @abstractmethod
    def get_image_url(self, html: str) -> str | None:
        ...

    def download_image(self, url) -> bool:
        """
        Downloads an image from a URL and saves it to a specified directory.
        
        Args:
            url (str): The URL of the image to download.
        """
        try:
            # Get the filename from the URL
            filename = os.path.basename(url.split("?")[0])

            # Construct the full path to save the file
            save_path = os.path.join(common.INPUT_SOURCES_IN, filename)

            # Define a User-Agent header to mimic a web browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }

            # Send a GET request with the headers
            response = requests.get(url, headers=headers, timeout=10)        
            
            # Check if the request was successful
            if response.status_code == 200:
                # Open the file in binary write mode and write the content
                with open(save_path, "wb") as file:
                    file.write(response.content)
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            common.error(f"An error occurred during the download: {e}")
        except Exception as e:
            common.error(f"An unexpected error occurred: {e}")

        return False

    @abstractmethod
    def read_html(self, url) -> str | None:
        ...

    def process_url(self, url: str) -> bool:
        html = self.read_html(url)
        if html:
            img_url = self.get_image_url(html)
            if img_url:
                if self.download_image(img_url):                    
                    return True
        return False

    def fetch(self, get_url: Callable[[int], str], min_year: int, max_count: int, remove: bool = False) -> int:
        max_fails: int = max_count // 2
        count: int = 0
        fails: int = 0
        
        if remove:
            common.remove_old(common.INPUT_SOURCES_IN)

        while count < max_count and fails <= max_fails:
            url: str = get_url(min_year)
            if url:
                if self.process_url(url):
                    count += 1
                else:
                    fails += 1
                    common.log(f"Unable to get {url}")
        return count
