import requests
import random
import re
import os
from io import BytesIO
from typing import Optional
from PIL import Image
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

class GoesGenerator(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        self.width = int(self.config.get("width", 1200))
        self.height = int(self.config.get("height", 1200))
        self.file_count = int(self.config.get("file_count", 1))
        self.base_filename = "noaa_goes"
        
        self.product_name = "GeoColor"
        self.product_id = "GEOCOLOR"

    def get_image_url_from_index(self, index_url: str) -> Optional[str]:
        try:
            response = requests.get(index_url, timeout=10)
            response.raise_for_status()
            
            match = re.search(r'href="([^"]+\.jpg)"', response.text)
            if match:
                return f"{index_url.rstrip('/')}/{match.group(1)}"
            else:
                self.log.error(f"No .jpg found in index: {index_url}")
                return None
        except Exception as e:
            self.log.error(f"Failed to parse index {index_url}: {e}")
            return None

    def _fetch_live_image(self) -> Optional[Image.Image]:
        index_url = f"{CDN_BASE}/{SATELLITE}/{SENSOR}/SECTOR/{SECTOR}/{self.product_id}/"
        
        image_url = self.get_image_url_from_index(index_url)
        if not image_url:
            return None
            
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            self.log.error(f"Failed to fetch image from {image_url}: {e}")
            return None

    def get_image(self) -> Image.Image:
        img = self._fetch_live_image()
        if img:
            return img
        return Image.new('RGB', (self.width, self.height), (0, 0, 0))

    def run(self, *args, **kwargs) -> None:
        out_dir = os.path.join(self.config["paths"]["generators_in"], "goes")
        os.makedirs(out_dir, exist_ok=True)
        
        product_items = list(PRODUCTS.items())
        
        for i in range(self.file_count):
            self.product_name, self.product_id = random.choice(product_items)
            self.log.info(f"Generating GOES-19 {SECTOR.upper()}: {self.product_name}")
            
            img = self.get_image()
            safe_product_name = self.product_name.replace(" ", "_")
            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}_{SECTOR}_{safe_product_name}.jpeg")
            
            try:
                img.save(filename)
                self.log.info(f"Saved GOES Image: {filename}")
            except Exception as e:
                self.log.error(f"Failed to save {filename}: {e}")
