from . import htmlInputSource
from .. import log
from bs4 import BeautifulSoup #type: ignore

DEFAULT_FILE_COUNT = 3

class Nasa(htmlInputSource.HtmlInputSource):
    def __init__(self, config: dict | None):
        if config:
            self.config = config.get("nasa", None)
            self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if self.config else DEFAULT_FILE_COUNT
            super().__init__(self.file_count)
        else:
            raise ValueError("No config for nasa!")

    def get_new_images(self, input_source: str):
        number_of_images: int = self.fetch(
                get_url=self.get_random_picture_url,
                input_source=input_source, 
                min_year=2002, 
                file_count=self.file_count)

        return number_of_images 

    def get_random_picture_url(self, min_year: int) -> str:
    # https://apod.nasa.gov/apod/ap220608.html
        date_str: str = self.get_random_date(min_year).strftime("%y%m%d")
        random_picture_url =f"https://apod.nasa.gov/apod/ap{date_str}.html"
        return random_picture_url

    def get_image_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")

        # Find the first <img> tag
        img_tag = soup.find('img')

        # Get the value of the 'src' attribute
        if img_tag:
            img_src = f"https://apod.nasa.gov/apod/{img_tag['src']}"
            return img_src
        else:
            log.error("No img tag with srcset attribute found.")
            return None
