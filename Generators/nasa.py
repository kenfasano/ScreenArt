from .htmlInputSource import HtmlInputSource
from bs4 import BeautifulSoup 

class Nasa(HtmlInputSource):
    def __init__(self):
        super().__init__()
        self.file_count = self.config.get("file_count", 3)

    def run(self, *args, **kwargs):
        self.log.info("Running NASA APOD Generator...")
        
        # Uses the fetch() contract implemented securely in HtmlInputSource
        number_of_images = self.fetch(
                get_url=self.get_random_picture_url,
                input_source="nasa", 
                min_year=2002, 
                file_count=self.file_count)

        self.log.info(f"Nasa got {number_of_images} files")
        return number_of_images 

    def get_random_picture_url(self, min_year: int) -> str:
        date_str: str = self.get_random_date(min_year).strftime("%y%m%d")
        return f"https://apod.nasa.gov/apod/ap{date_str}.html"

    def get_image_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find('img')

        if img_tag:
            return f"https://apod.nasa.gov/apod/{img_tag['src']}"
        else:
            self.log.error("No img tag found in APOD html.")
            return None
