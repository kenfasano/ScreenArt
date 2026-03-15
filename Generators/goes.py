import requests
from requests.adapters import HTTPAdapter
import socket
import random
import re
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from .drawGenerator import DrawGenerator

CDN_BASE = "https://cdn.star.nesdis.noaa.gov"
SATELLITE = "GOES19"
SENSOR = "ABI"
SECTOR = "se"

PRODUCTS = {
    "GeoColor": "GEOCOLOR",
    "Sandwich RGB": "Sandwich",
    "Air Mass": "AirMass",
    "Day Night Cloud Micro": "DayNightCloudMicroCombo",
    "Dust": "Dust",
    "Fire Temperature": "FireTemperature"
}

MAX_WORKERS = 6  # max is len(PRODUCTS)

class GoesGenerator(DrawGenerator):
    def __init__(self):
        super().__init__()

        self.width = int(self.config.get("width", 1200))
        self.height = int(self.config.get("height", 1200))
        self.file_count = int(self.config.get("file_counts", {}).get("goes", 1))
        self.base_filename = "noaa_goes"

        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=min(MAX_WORKERS, self.file_count),
            max_retries=0
        )
        self.session.mount("https://", adapter)
        socket.getaddrinfo("cdn.star.nesdis.noaa.gov", 443)  # warm DNS cache

    def _get_image_url_from_index(self, index_url: str) -> Optional[str]:
        try:
            response = self.session.get(index_url, timeout=10)
            response.raise_for_status()
            match = re.search(r'href="([^"]+\.jpg)"', response.text)
            if match:
                return f"{index_url.rstrip('/')}/{match.group(1)}"
            self.log.debug(f"No .jpg found in index: {index_url}")
            return None
        except Exception as e:
            self.log.debug(f"Failed to parse index {index_url}: {e}")
            return None

    def _fetch_and_save(self, i: int, product_name: str, product_id: str) -> None:
        index_url = f"{CDN_BASE}/{SATELLITE}/{SENSOR}/SECTOR/{SECTOR}/{product_id}/"
        image_url = self._get_image_url_from_index(index_url)
        if not image_url:
            return

        try:
            response = self.session.get(image_url, timeout=15)
            response.raise_for_status()

            out_dir = os.path.join(self.config["paths"]["generators_in"], "goes")
            safe_name = product_name.replace(" ", "_")
            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}_{SECTOR}_{safe_name}.jpeg")

            # Save raw bytes — skip PIL decode/re-encode
            with open(filename, "wb") as f:
                f.write(response.content)
            self.log.debug(f"Saved GOES Image: {filename}")
        except Exception as e:
            self.log.debug(f"Failed to fetch/save {image_url}: {e}")

    def run(self, *args, **kwargs) -> None:
        out_dir = os.path.join(self.config["paths"]["generators_in"], "goes")
        os.makedirs(out_dir, exist_ok=True)

        selected = random.sample(list(PRODUCTS.items()), min(self.file_count, len(PRODUCTS)))

        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, self.file_count)) as executor:
            for i, (product_name, product_id) in enumerate(selected):
                executor.submit(self._fetch_and_save, i, product_name, product_id)
