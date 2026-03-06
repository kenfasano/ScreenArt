import random
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import re
import time
from io import BytesIO
from typing import Any
from PIL import Image
from urllib.parse import unquote

from .drawGenerator import DrawGenerator

class Wiki(DrawGenerator):
    def __init__(self):
        super().__init__()

        self.width = int(self.config.get("width", 1920))
        self.height = int(self.config.get("height", 1080))
        self.file_count = int(self.config.get("wiki", {}).get("file_count", 1))
        self.base_filename = "wiki"

        default_keywords = ["nature", "space", "cathedrals", "Native American", "Indigenous", "Buddhism"]
        keyword_file = self.config.get("keyword_file")
        if keyword_file:
            try:
                with open(keyword_file, "r", encoding="utf-8") as f:
                    self.keywords = [line.strip() for line in f if line.strip()]
            except Exception:
                self.keywords = default_keywords
        else:
            self.keywords = default_keywords

        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "ScreenArt/1.0 (kenfasano@hotmail.com)",
            "Referer": "https://commons.wikimedia.org/"
        }

        # Session pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # --------------------------------------------------------
    # SEARCH QUERY BUILDER (75% keywords / 25% random)
    # --------------------------------------------------------

    def _build_search_query(self) -> str:
        if random.random() < 0.75:
            sample_size = min(5, len(self.keywords))
            chosen = random.sample(self.keywords, sample_size)
            return " OR ".join(chosen)
        return "random"

    # --------------------------------------------------------
    # SINGLE SEARCH CALL
    # --------------------------------------------------------

    def fetch_fresh_data(self) -> list[dict]:
        keywords = self._build_search_query()

        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": 1600, # self.width,
        }

        if keywords == "random":
            params.update({
                "generator": "random",
                "grnnamespace": 6,
                "grnlimit": 20,
            })
        else:
            params.update({
                "generator": "search",
                "gsrnamespace": 6,
                "gsrsearch": keywords,
                "gsrlimit": 100,
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
                    img = Image.open(BytesIO(resp.content)).convert("RGB")
                    return self._aspect_fill(img)

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

    # --------------------------------------------------------

    def _aspect_fill(self, img: Image.Image) -> Image.Image:
        target_ratio = self.width / self.height
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_height = self.height
            new_width = int(new_height * img_ratio)
        else:
            new_width = self.width
            new_height = int(new_width / img_ratio)

        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - self.width) / 2
        top = (new_height - self.height) / 2
        return img.crop((left, top, left + self.width, top + self.height))

    def get_short_name(self, url: str) -> str:
        filename = unquote(os.path.basename(url))
        clean_name = re.sub(r"[^\w\-_\. ]", "_", filename)
        return os.path.splitext(clean_name)[0][:15]

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(self, *args, **kwargs) -> None:
        out_dir = os.path.join(self.config["paths"]["generators_in"], "wiki")
        os.makedirs(out_dir, exist_ok=True)

        items = self.fetch_fresh_data()
        if not items:
            return

        selected = random.sample(
            items,
            min(self.file_count, len(items))
        )

        def download_worker(info: dict):
            url = info.get("thumburl", info.get("url"))
            if not url:
                return

            img = self.download_and_process(url)
            if img:
                name = self.get_short_name(url)
                filename = os.path.join(out_dir, f"{name}.jpeg").replace("1920px-", "")
                try:
                    img.save(filename, quality=95)
                    self.log.debug(f"Saved Wiki Image: {filename}")
                except Exception as e:
                    self.log.debug(f"Failed saving {filename}: {e}")

        # Parallel downloads (I/O bound)
        with ThreadPoolExecutor(max_workers=12) as executor:
            executor.map(download_worker, selected)
