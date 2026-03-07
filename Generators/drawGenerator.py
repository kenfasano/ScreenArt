import os
import hashlib
import requests
from requests.adapters import HTTPAdapter
import socket
from io import BytesIO
from typing import Optional
from PIL import Image

from .generator import Generator

class DrawGenerator(Generator):
    def __init__(self):
        super().__init__()
        self.cache_dir = self.config.get("paths", {}).get("cache_dir", os.path.join(self.base_path, "cache"))
        os.makedirs(self.cache_dir, exist_ok=True)

        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=16,  # tiles fetched in parallel by subclasses
            max_retries=0
        )
        self.session.mount("https://", adapter)

    def get_cached_image(self, url: str, cache_dir: Optional[str] = None) -> Optional[Image.Image]:
        active_cache_dir = cache_dir if cache_dir else self.cache_dir
        os.makedirs(active_cache_dir, exist_ok=True)

        hash_object = hashlib.md5(url.encode())
        filepath = os.path.join(active_cache_dir, f"{hash_object.hexdigest()}.jpg")

        if os.path.exists(filepath):
            try:
                self.log.debug(f"Loaded cached image from {filepath}")
                return Image.open(filepath)
            except Exception as e:
                self.log.debug(f"Error reading cache file {filepath}: {e}")
                return None

        try:
            self.log.debug(f"Downloading new image to cache: {url}")
            response = self.session.get(url, stream=True, timeout=10)

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img.convert('RGB').save(filepath)
                self.log.debug(f"Saved downloaded image to {filepath}")
                return img
            else:
                self.log.debug(f"Failed to fetch {url} - Status: {response.status_code}")
                return None

        except Exception as e:
            self.log.debug(f"Error downloading {url}: {e}")
            return None
