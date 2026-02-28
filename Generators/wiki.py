import random
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import re
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
        self.log.debug(f"{self.file_count=}")
        self.base_filename = "wiki"
        
        keyword_file = self.config.get("keyword_file")
        if keyword_file:
            try:
                with open(keyword_file, 'r', encoding='utf-8') as f:
                    self.keywords = [line.strip() for line in f if line.strip()]
            except Exception:
                self.keywords = ["nature", "space", "cathedrals", "Native American", "Indigenous", "Buddhism"]
        else:
            self.keywords = ["nature", "space", "cathedrals", "Native American", "Indigenous", "Buddhism"]

        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.headers = {
            "User-Agent": "ScreenArt/1.0 (kenfasano@hotmail.com)",
            "Referer": "https://commons.wikimedia.org/"
        }

    def _get_random_keyword(self) -> str:
        if random.randint(1,4) < 4:
            return random.choice(self.keywords)
        return "random"

    def fetch_fresh_data(self, keyword: str) -> list[dict]:
        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|mime|size",
            "iiurlwidth": self.width
        }

        if keyword == "random":
            params.update({
                "generator": "random",
                "grnnamespace": 6,
                "grnlimit": 20 
            })
        else:
            params.update({
                "generator": "search",
                "gsrnamespace": 6,
                "gsrsearch": keyword,
                "gsrlimit": 500 
            })

        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=15)
            if response.status_code == 200:
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
            else:
                self.log.debug(f"API Error: {response.status_code}")
                return []
        except Exception as e:
            self.log.debug(f"Fetch error: {e}")
            return []

    def get_image_url(self, keyword: str) -> str | None:
        items = self.fetch_fresh_data(keyword)
        if items:
            choice = random.choice(items)
            return choice.get("thumburl", choice.get("url"))
        return None

    def download_and_process(self, url: str) -> tuple[Image.Image | None, int]:
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                return self._aspect_fill(img), resp.status_code
            elif resp.status_code == 429:
                self.log.debug("Hit 429 on Image Download. (Search API was spared).")
                return None, 429
            return None, resp.status_code
        except Exception as e:
            self.log.debug(f"{e}")
            return None, -1

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
        # Safely remove illegal characters without common.py
        clean_name = re.sub(r'[^\w\-_\. ]', '_', filename)
        return os.path.splitext(clean_name)[0][:15]

    def run(self, *args, **kwargs) -> None:
        with self.timer():
            out_dir = os.path.join(self.config["paths"]["generators_in"], "wiki")
            os.makedirs(out_dir, exist_ok=True)

            def process_single_image(_):
                """Worker function for a single iteration of the loop"""
                keyword = self._get_random_keyword()
                url = self.get_image_url(keyword)
                
                if url:
                    img, _ = self.download_and_process(url)
                    if img:
                        name = self.get_short_name(url)
                        filename = os.path.join(out_dir, f"{name}.jpeg").replace("1920px-", "")
                        try:
                            img.save(filename)
                            self.log.debug(f"Saved Wiki Image: {filename}")
                        except Exception as e:
                            self.log.debug(f"Failed to save {filename}: {e}")

            # Use ThreadPoolExecutor to run iterations in parallel
            # max_workers=5 to 10 is usually a safe starting point for network tasks
            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(process_single_image, range(self.file_count))
