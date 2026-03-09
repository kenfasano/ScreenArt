from .source import Source
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
import socket
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

        # Session pooling with connection reuse
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        candidate_count = self.file_count * self.CANDIDATE_MULTIPLIER
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=min(self.MAX_WORKERS, candidate_count),
            max_retries=0
        )
        self.session.mount("https://", adapter)
        socket.getaddrinfo("apod.nasa.gov", 443)  # warm DNS cache

    MIN_YEAR = 2002
    INPUT_SOURCE = "nasa"
    MAX_WORKERS = 5
    CANDIDATE_MULTIPLIER = 3

    def _apod_url(self) -> str:
        date_str = self.get_random_date(self.MIN_YEAR).strftime("%y%m%d")
        return f"https://apod.nasa.gov/apod/ap{date_str}.html"

    def _get_image_url(self, page_url: str) -> str | None:
        try:
            response = self.session.get(page_url, timeout=10)
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
        try:
            filename = os.path.basename(img_url.split("?")[0])
            out_dir = os.path.join(self.config["paths"]["generators_in"], self.INPUT_SOURCE)
            os.makedirs(out_dir, exist_ok=True)

            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()

            with open(os.path.join(out_dir, filename), "wb") as f:
                f.write(response.content)
            self.log.debug(f"Downloaded {img_url}")
            return True
        except Exception as e:
            self.log.debug(f"Download failed for {img_url}: {e}")
            return False

    def _fetch_one(self, page_url: str) -> bool:
        img_url = self._get_image_url(page_url)
        return self._download_image(img_url) if img_url else False

    def run(self, *args, **kwargs) -> int:
        candidates = [self._apod_url() for _ in range(self.file_count * self.CANDIDATE_MULTIPLIER)]
        fetched = 0

        with ThreadPoolExecutor(max_workers=min(self.MAX_WORKERS, len(candidates))) as executor:
            futures = {executor.submit(self._fetch_one, url): url for url in candidates}
            for future in as_completed(futures):
                if future.result():
                    fetched += 1
                if fetched >= self.file_count:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

        return fetched
