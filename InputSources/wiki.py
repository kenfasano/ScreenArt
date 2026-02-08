from . import htmlInputSource
from .. import log
from bs4 import BeautifulSoup

DEFAULT_FILE_COUNT = 3

class Wiki(htmlInputSource.HtmlInputSource):
    def __init__(self, config: dict | None):
        if config:
            self.config = config.get("wiki", None)
            if self.config:
                self.file_count = self.config.get("file_count", DEFAULT_FILE_COUNT) if config else DEFAULT_FILE_COUNT
                super().__init__(self.file_count)
            else:
                self.file_count = DEFAULT_FILE_COUNT 
        else:
            raise ValueError("No config for wiki!")

    def get_random_picture_url(self, min_year: int) -> str:
        date_str: str = self.get_random_date(min_year).strftime("%Y-%m-%d")
        # https://commons.wikimedia.org/wiki/Commons:Picture_of_the_day#26
        random_picture_url = f"https://commons.wikimedia.org/wiki/Template:Potd/{date_str}"
        return random_picture_url

    def get_new_images(self, input_source: str) -> int:
        new_images_count: int = self.fetch(
            get_url=self.get_random_picture_url, 
            input_source=input_source, 
            min_year=2002, 
            file_count=self.file_count)

        return new_images_count

    def get_image_url(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        # Find the <img> tag that has a "srcset" attribute
        img_tag = soup.find("img", srcset=True)
        # Check if the img tag was found
        if img_tag:
            # Get the value of the "srcset" attribute
            srcset_value = img_tag["srcset"]

            # The srcset value is a string with comma-separated URLs and descriptors.
            # Split the string by the comma.
            if srcset_value:
                urls_with_descriptors = srcset_value.split(",")
                if not urls_with_descriptors:
                    log.error("urls_with_descriptors is empty!")
            else:
                log.error("srcset_value is empty!")

            # The first item in the split list will be the first URL and its descriptor.
            # You need to split this by space to get just the URL.
            first_url_with_descriptor = urls_with_descriptors[0].strip()

            # Split by space and take the first part, which is the URL
            first_url = first_url_with_descriptor.split(" ")[0]
            
            return first_url
        else:
            log.error("No img tag with srcset attribute found.")
            return None
