import requests
import random
import re
from io import BytesIO
from typing import Optional
from PIL import Image
from . import drawGenerator
from .. import log
from .. import common
from typing import Any # Import Any for flexible dicts

# --- Constants ---

# NOAA CDN Base URL
CDN_BASE = "https://cdn.star.nesdis.noaa.gov"
SATELLITE = "GOES19"
SENSOR = "ABI"
SECTOR = "se"       # Southeast Sector

# Mapping friendly names to the URL product directory names.
# Note: Case sensitivity matters for these URLs.
PRODUCTS = {
    "GeoColor": "GEOCOLOR", 
    "Sandwich RGB": "Sandwich",
    "Air Mass": "AirMass",
    "Day Night Cloud Micro": "DayNightCloudMicroCombo",
    "Dust": "Dust",
    "Fire Temperature": "FireTemperature"
}

class GoesGenerator(drawGenerator.DrawGenerator):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config, "goes")
        
        # Configuration
        self.width = int(self.config.get("width", 1200))
        self.height = int(self.config.get("height", 1200))
        self.file_count = int(self.config.get("file_count", 1))
        self.base_filename = "noaa_goes"
        
        # State
        self.product_name = "GeoColor"
        self.product_id = "GEOCOLOR"

    def get_image_url_from_index(self, index_url: str) -> Optional[str]:
        """
        Parses the NOAA directory listing to find the first .jpg link.
        This usually targets '1200x1200.jpg' based on standard NOAA indexing.
        """
        try:
            log.info(f"Checking index: {index_url}")
            response = requests.get(index_url, timeout=10)
            response.raise_for_status()
            
            # Regex to find the first href ending in .jpg
            # Pattern looks for: href="filename.jpg"
            match = re.search(r'href="([^"]+\.jpg)"', response.text)
            
            if match:
                filename = match.group(1)
                full_url = f"{index_url.rstrip('/')}/{filename}"
                return full_url
            else:
                log.error(f"No .jpg found in index: {index_url}")
                return None
                
        except Exception as e:
            log.error(f"Failed to parse index {index_url}: {e}")
            return None

    def _fetch_live_image(self) -> Optional[Image.Image]:
        """
        1. Determines the index URL for the current product.
        2. Scrapes the specific image filename.
        3. Downloads and returns the image.
        """
        # Build the Directory URL (e.g. .../SECTOR/se/GEOCOLOR/)
        index_url = (
            f"{CDN_BASE}/{SATELLITE}/{SENSOR}/SECTOR/{SECTOR}/"
            f"{self.product_id}/"
        )
        
        # 1. Find the actual file URL
        image_url = self.get_image_url_from_index(index_url)
        if not image_url:
            return None
            
        # 2. Download the Image
        try:
            log.info(f"Fetching GOES image: {image_url}")
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            
            image_data = BytesIO(response.content)
            img = Image.open(image_data)
            return img.convert("RGB")
            
        except Exception as e:
            log.error(f"Failed to fetch image from {image_url}: {e}")
            return None

    def get_image(self) -> Image.Image:
        """Retrieves and processes the image."""
        img = self._fetch_live_image()
        
        if img:
            return img
        
        # Return a blank black image on failure
        return Image.new('RGB', (self.width, self.height), (0, 0, 0))

    def draw(self) -> None:
        """Cycle through a random selection of products and save them."""
        product_items = list(PRODUCTS.items())
        
        for i in range(self.file_count):
            # 1. Pick a Random Product
            self.product_name, self.product_id = random.choice(product_items)

            log.info(f"Generating GOES-19 {SECTOR.upper()}: {self.product_name}")
            
            # 2. Get Image
            img = self.get_image()
            
            # 3. Save
            safe_product_name = self.product_name.replace(" ", "_")
            filename = f"{self.paths["goes_out"]}/{self.base_filename}_{i+1}_{SECTOR}_{safe_product_name}.jpeg"
            
            img.save(filename, 'JPEG')
            log.info(f"Saved GOES Image: {filename}")
