import random
import requests # type: ignore
import json
import os
import time
from io import BytesIO
from typing import Optional, Dict, Any, List
from PIL import Image

from . import drawGenerator
from .. import common
from .. import log
from urllib.parse import unquote

class Wiki(drawGenerator.DrawGenerator):
    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = common.get_config(config, "wiki")
        
        self.width = int(self.config.get("width", 1920))
        self.height = int(self.config.get("height", 1080))
        self.file_count = int(self.config.get("file_count", 1))
        self.base_filename = "wiki"
        
        # Define Cache Directory on your SSD
        self.cache_dir = common.WIKI_CACHE
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            log.info(f"Created cache directory: {self.cache_dir}")

        # Load Keywords
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
        # 25% chance of random, 75% chance of specific keyword
        if random.randint(1,4) < 4:
            return random.choice(self.keywords)
        return "random"

    def _fetch_fresh_data(self, keyword: str) -> List[Dict]:
        """Hit the API to get 500 items and save to disk."""
        log.info(f"Cache miss for '{keyword}'. Fetching from API...")
        
        params: Dict[str, Any] = {
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
                "grnlimit": 20  # Keep random small/fresh
            })
        else:
            params.update({
                "generator": "search",
                "gsrnamespace": 6,
                "gsrsearch": keyword,
                "gsrlimit": 500  # REQUEST 500 ITEMS
            })

        try:
            response = requests.get(self.api_url, params=params, headers=self.headers, timeout=15)
            if response.status_code == 200:
#                self.wiki_log.write(f"[{common.get_timestamp()}] Fetch fresh data: {response.status_code}\n")

                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                page_list = list(pages.values())
                
                # Filter useful images immediately
                clean_list = []
                for p in page_list:
                    if "imageinfo" in p:
                        info = p["imageinfo"][0]
                        # Basic validation
                        if "image" in info.get("mime", "") and "svg" not in info.get("mime", ""):
                            clean_list.append(info)
                
                # Save to cache if it's not a "random" search
                if keyword != "random" and clean_list:
                    CACHE_PATH = os.path.join(self.cache_dir, f"wiki_{keyword}.json")
                    with open(CACHE_PATH, 'w') as f:
                        json.dump(clean_list, f)
                    log.info(f"Cached {len(clean_list)} items to {CACHE_PATH}")
                
                return clean_list
            else:
                log.warning(f"API Error: {response.status_code}")
#                self.wiki_log.write(f"[{common.get_timestamp()}] Fetch fresh data: {response.status_code}\n")
                return []
        except Exception as e:
            log.error(f"Fetch error: {e}")
#            self.wiki_log.write(f"[{common.get_timestamp()}] Fetch fresh data: fetch error: {e}\n")
            return []

    def _get_image_url_from_cache(self, keyword: str) -> Optional[str]:
        """Try to load from disk, fallback to API."""
        CACHE_PATH = os.path.join(self.cache_dir, f"wiki_{keyword}.json")
        items = []

        # 1. Try to load local cache
        if keyword != "random" and os.path.exists(CACHE_PATH):
            try:
                # OPTIONAL: Check file age. If > 7 days, ignore it to force refresh.
                file_age = time.time() - os.path.getmtime(CACHE_PATH)
                if file_age > (86400 * 7): # 7 days
                    log.info(f"Cache for {keyword} is old ({int(file_age/86400)} days). Refreshing.")
                    items = [] # Force refresh
                else:
                    with open(CACHE_PATH, 'r') as f:
                        items = json.load(f)
            except Exception as e:
                log.warning(f"Cache read error: {e}")

        # 2. If no local items, fetch from API
        if not items:
            items = self._fetch_fresh_data(keyword)

        # 3. Pick a random item
        if items:
            choice = random.choice(items)
            return choice.get("thumburl", choice.get("url"))
        
        return None

    def _download_and_process(self, url: str) -> tuple[Optional[Image.Image], int]:
        try:
            # Simple download
            resp = requests.get(url, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                return self._aspect_fill(img), resp.status_code
            elif resp.status_code == 429:
                log.warning("Hit 429 on Image Download. (Search API was spared).")
                return None, 429
        except Exception as e:
            log.warning(f"{e}")
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
        filename = common.fix_file_name(os.path.basename(url))
        return os.path.splitext(unquote(filename))[0][:15]

    def draw(self) -> None:
        log.info(f"draw - {self.file_count=}")

#        with open("/Users/kenfasano/Scripts/ScreenArt/wiki.log", "a") as self.wiki_log:
        for _ in range(self.file_count):
            keyword = self._get_random_keyword()
            
            # This now hits the SSD, not the API (mostly)
            url = self._get_image_url_from_cache(keyword)
            
            if url:
                img, status_code = self._download_and_process(url)
                name = self.get_short_name(url)
                filename = f"{common.GENERATORS_IN}/Wiki/{name}.jpeg"

                if img:
                    img.save(filename, 'JPEG')
                    log.info(f"Saved: {filename}")
#                    self.wiki_log.write(f"[{common.get_timestamp()}] {filename} - {status_code}\n")
                else:
                    log.warning("Image download failed")
#                    self.wiki_log.write(f"{filename} - {status_code}\n")
            
            # Still good to sleep briefly between actual image downloads
            time.sleep(1)
