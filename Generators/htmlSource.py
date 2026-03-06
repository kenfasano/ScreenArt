from abc import abstractmethod

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

