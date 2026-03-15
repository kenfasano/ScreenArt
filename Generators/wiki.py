import requests
from requests.adapters import HTTPAdapter
import socket
import os
from concurrent.futures import ThreadPoolExecutor
import re
import time
from typing import Any
from PIL import Image
from urllib.parse import unquote

from .drawGenerator import DrawGenerator

MAX_WORKERS = 10

class Wiki(DrawGenerator):
    def __init__(self):
        super().__init__()

        self.file_count = int(self.config.get("file_counts", {}).get("wiki", 6))
        self.out_dir = os.path.join(self.config["paths"]["generators_in"], "wiki")
        os.makedirs(self.out_dir, exist_ok=True)

        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "ScreenArt/1.0 (kenfasano@hotmail.com)",
            "Referer": "https://commons.wikimedia.org/"
        }

        # Session pooling
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=self.file_count,  # match worker count
            max_retries=0  # you handle retries manually
        )
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)
        socket.getaddrinfo("upload.wikimedia.org", 443)  # warms OS DNS cache

    # --------------------------------------------------------
    # SEARCH QUERY BUILDER (75% keywords / 25% random)
    # --------------------------------------------------------
    # SINGLE SEARCH CALL
    # --------------------------------------------------------

    def fetch_fresh_data(self) -> list[dict]:
        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1600, # self.width,
        }

        params.update({
            "generator": "random",
            "grnnamespace": 6,
            "grnlimit": self.file_count,
        })

        try:
            response = self.session.get(self.api_url, params=params, timeout=15)
            if response.status_code != 200:
                self.log.debug(f"API error: {response.status_code}")
                return []

            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            page_list = list(pages.values())

            clean_list = []
            for p in page_list:
                if "imageinfo" in p:
                    info = p["imageinfo"][0]
                    if "image" in info.get("mime", "") and "svg" not in info.get("mime", ""):
                        clean_list.append(info)

            return clean_list

        except Exception as e:
            self.log.debug(f"Fetch error: {e}")
            return []

    # --------------------------------------------------------
    # DOWNLOAD WITH SIMPLE BACKOFF
    # --------------------------------------------------------

    def download_and_process(self, url: str, retries: int = 3) -> Image.Image | None:
        backoff = 1

        for attempt in range(retries):
            try:
                resp = self.session.get(url, timeout=15)

                if resp.status_code == 200:
                    name = self.get_short_name(url)
                    filename = os.path.join(self.out_dir, f"{name}.jpeg").replace("1920px-", "")
                    with open(filename, "wb") as f:
                        f.write(resp.content)

                if resp.status_code == 429:
                    self.log.debug("429 received. Backing off...")
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                return None

            except Exception as e:
                self.log.debug(f"Download error: {e}")
                time.sleep(backoff)
                backoff *= 2

        return None

    def get_short_name(self, url: str) -> str:
        filename = unquote(os.path.basename(url))
        clean_name = re.sub(r"[^\w\-_\. ]", "_", filename)
        return os.path.splitext(clean_name)[0][:15]

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(self, *args, **kwargs) -> None:
        items = self.fetch_fresh_data()
        if not items:
            return

        #selected = random.sample(
        #    items,
        #    min(self.file_count, len(items))
        #)
        selected = items

        def download_worker(info: dict):
            url = info.get("thumburl", info.get("url"))
            if not url:
                return
            self.download_and_process(url)

        # Parallel downloads (I/O bound)
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, self.file_count)) as executor:
            executor.map(download_worker, selected)
