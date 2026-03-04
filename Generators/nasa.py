from .source import Source
from bs4 import BeautifulSoup
import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class Nasa(Source):
    def __init__(self):
        super().__init__()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.file_count = self.config.get("nasa", {}).get("file_count", 3)
        self.log.debug(f"{self.file_count=}")

    MIN_YEAR = 2002
    INPUT_SOURCE = "nasa"
    MAX_WORKERS = 5
    # Fetch more candidates than needed to account for pages with no image
    CANDIDATE_MULTIPLIER = 3

    def _apod_url(self) -> str:
        date_str = self.get_random_date(self.MIN_YEAR).strftime("%y%m%d")
        return f"https://apod.nasa.gov/apod/ap{date_str}.html"

    def _get_image_url(self, page_url: str) -> str | None:
        """Fetch an APOD page and return the full image URL, or None if absent/SVG."""
        try:
            response = requests.get(page_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log.debug(f"Error fetching {page_url}: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.find("img")
        if not img_tag:
            self.log.debug(f"No <img> tag found: {page_url}")
            return None

        img_url = f"https://apod.nasa.gov/apod/{img_tag['src']}"
        if "svg" in img_url:
            self.log.debug(f"Skipping SVG: {img_url}")
            return None

        return img_url

    def _download_image(self, img_url: str) -> bool:
        """Download an image to the configured output directory."""
        try:
            filename = os.path.basename(img_url.split("?")[0])
            out_dir = os.path.join(self.config["paths"]["generators_in"], self.INPUT_SOURCE)
            os.makedirs(out_dir, exist_ok=True)

            response = requests.get(img_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            with open(os.path.join(out_dir, filename), "wb") as f:
                f.write(response.content)
            self.log.debug(f"Downloaded {img_url}")
            return True
        except Exception as e:
            self.log.debug(f"Download failed for {img_url}: {e}")
            return False

    def _fetch_one(self, page_url: str) -> bool:
        """Try to download the image from one APOD page. Returns True on success."""
        img_url = self._get_image_url(page_url)
        return self._download_image(img_url) if img_url else False

    def run(self, *args, **kwargs):
        with self.timer():
            # Generate extra candidates upfront so missing-image pages don't stall us
            candidates = [self._apod_url() for _ in range(self.file_count * self.CANDIDATE_MULTIPLIER)]
            fetched = 0

            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                futures = {executor.submit(self._fetch_one, url): url for url in candidates}
                for future in as_completed(futures):
                    if future.result():
                        fetched += 1
                    if fetched >= self.file_count:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

            return fetched
