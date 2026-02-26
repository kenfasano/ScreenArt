from .htmlSource import HtmlSource
from bs4 import BeautifulSoup 
import time

class Nasa(HtmlSource):
    def __init__(self):
        super().__init__()
        self.file_count = self.config.get("nasa", {}).get("file_count", 3)
        self.log.info(f"{self.file_count=}")

    def run(self, *args, **kwargs):
        self.log.info("Running NASA APOD Generator...")
        start_time = time.perf_counter()
        
        # Uses the fetch() contract implemented securely in HtmlSource
        number_of_images = self.fetch(
                self.get_random_picture_url,
                input_source="nasa", 
                min_year=2002, 
                file_count=self.file_count)

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        self.log.info(f"Nasa: {elapsed_ms:.2f}ms")

        self.log.info(f"Nasa got {number_of_images} files")
        return number_of_images 

    def get_random_picture_url(self, min_year: int) -> str:
        date_str: str = self.get_random_date(min_year).strftime("%y%m%d")
        self.url = f"https://apod.nasa.gov/apod/ap{date_str}.html"
        return self.url

    def get_image_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find('img')

        if img_tag:
            self.log.info(f"Got img tag for {self.url}")
            return f"https://apod.nasa.gov/apod/{img_tag['src']}"
        else:
            self.log.error(f"No img tag found in APOD html for {self.url}")
            return None
