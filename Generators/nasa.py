from .htmlSource import HtmlSource
from bs4 import BeautifulSoup 

class Nasa(HtmlSource):
    def __init__(self):
        super().__init__()
        self.file_count = self.config.get("nasa", {}).get("file_count", 3)
        self.log.debug(f"{self.file_count=}")

    def run(self, *args, **kwargs):
        with self.timer():
            # Uses the fetch() contract implemented securely in HtmlSource
            number_of_images = self.fetch(
                    self.get_random_picture_url,
                    input_source="nasa", 
                    min_year=2002, 
                    file_count=self.file_count)
            return number_of_images 

    def get_random_picture_url(self, min_year: int) -> str:
        date_str: str = self.get_random_date(min_year).strftime("%y%m%d")
        self.url = f"https://apod.nasa.gov/apod/ap{date_str}.html"
        return self.url

    def get_image_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find('img')

        if img_tag:
            self.log.debug(f"Got img tag for {self.url}")
            return f"https://apod.nasa.gov/apod/{img_tag['src']}"
        else:
            self.log.debug(f"No img tag found in APOD html for {self.url}")
            return None
