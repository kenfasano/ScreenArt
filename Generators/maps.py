from . import drawGenerator
from .. import log
from PIL import Image  # type: ignore
from astral import LocationInfo
from astral.sun import sun           
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any # Import Any for flexible dicts
from typing import Optional
from typing import Tuple, Optional
from datetime import datetime
import hashlib
import math
import os
import pytz                          
import random
import requests

def is_night_at_location(lat, lon):
    """
    Returns True if the sun is below the horizon at the given coordinates.
    """
    # 1. Get current time in UTC (Astral calculations work best in UTC)
    now_utc = datetime.now(pytz.utc)
    
    # 2. Define the location (City name/Region aren't strictly needed for math, just lat/lon)
    city = LocationInfo("Target City", "Region", "UTC", lat, lon)
    
    # 3. Calculate sun times for *today* at that location
    # Note: We wrap this in a try/except because polar regions (24hr day/night) can raise errors
    try:
        s = sun(city.observer, date=now_utc, tzinfo=pytz.utc)
        sunrise = s['sunrise']
        sunset = s['sunset']
        
        # 4. Check if we are in the night period
        # Night is defined as: Time is before Sunrise OR Time is after Sunset
        if now_utc < sunrise or now_utc > sunset:
            return True
        else:
            return False
            
    except Exception as e:
        # Fallback for edge cases (e.g., polar circles) or calculation errors
        print(f"Astral calculation error: {e}")
        return False

# --- Data Constants ---

CITIES = {
    "West Palm Beach, FL": (26.7153, -80.0534),
    "Tokyo, Japan": (35.6762, 139.6503),
    "Delhi, India": (28.7041, 77.1025),
    "Shanghai, China": (31.2304, 121.4737),
    "Sao Paulo, Brazil": (-23.5505, -46.6333),
    "Mexico City, Mexico": (19.4326, -99.1332),
    "Cairo, Egypt": (30.0444, 31.2357),
    "Mumbai, India": (19.0760, 72.8777),
    "Beijing, China": (39.9042, 116.4074),
    "Dhaka, Bangladesh": (23.8103, 90.4125),
    "Osaka, Japan": (34.6937, 135.5023),
    "New York, USA": (40.7128, -74.0060),
    "Karachi, Pakistan": (24.8607, 67.0011),
    "Buenos Aires, Argentina": (-34.6037, -58.3816),
    "Istanbul, Turkey": (41.0082, 28.9784),
    "Manila, Philippines": (14.5995, 120.9842),
    "Lagos, Nigeria": (6.5244, 3.3792),
    "Rio de Janeiro, Brazil": (-22.9068, -43.1729),
    "Kinshasa, DR Congo": (-4.4419, 15.2663),
    "Los Angeles, USA": (34.0522, -118.2437),
    "Moscow, Russia": (55.7558, 37.6173),
    "Paris, France": (48.8566, 2.3522),
    "London, UK": (51.5074, -0.1278),
    "Bangkok, Thailand": (13.7563, 100.5018),
    "Jakarta, Indonesia": (-6.2088, 106.8456),
    "Seoul, South Korea": (37.5665, 126.9780),
    "Sydney, Australia": (-33.8688, 151.2093),
    "Cape Town, South Africa": (-33.9249, 18.4241)
}

LAYERS = {
    "True Color": ("VIIRS_SNPP_CorrectedReflectance_TrueColor", 9),
    "Night Lights": ("VIIRS_SNPP_DayNightBand_ENCC", 8),
    "Vegetation (False Color)": ("VIIRS_SNPP_CorrectedReflectance_BandsM11-I2-I1", 9),
    "Surface Temp (Day)": ("MODIS_Terra_Land_Surface_Temp_Day", 7),
    "Chlorophyll": ("MODIS_Terra_Chlorophyll_A", 7)
}

class NasaMapGenerator(drawGenerator.DrawGenerator):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config, "maps")
        log.info(f"{self.config=}")
        
        # Standard Configuration
        self.width = int(self.config.get("width", 1920))
        self.height = int(self.config.get("height", 1080))
        self.file_count = int(self.config.get("file_count", 1))
        self.base_filename = "nasa_earth"
        
        # Defaults (Will be overwritten in draw loop)
        self.grid_size = 3
        self.tile_size = 256
        self.zoom = 4
        self.lat = 0.0
        self.lon = 0.0
        self.layer_id = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
        
        # Date Logic
        today = datetime.today()
        self.date_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    def _lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        """Standard Web Mercator projection logic."""
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
        return xtile, ytile

    def get_cached_image(self, url: str, cache_dir: str = "cache") -> Optional[Image.Image]:
        """
        Checks if an image exists in the local cache.
        If yes: loads it from disk.
        If no: downloads it, saves it to disk, then loads it.
        """
        
        # 1. Ensure cache directory exists
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # 2. Create a safe filename from the URL
        # We use an MD5 hash of the URL to ensure a unique filename 
        # that doesn't contain illegal filesystem characters.
        hash_object = hashlib.md5(url.encode())
        filename = f"{hash_object.hexdigest()}.jpg"
        filepath = os.path.join(cache_dir, filename)

        # 3. Check if file exists locally
        if os.path.exists(filepath):
            try:
                return Image.open(filepath)
            except Exception as e:
                print(f"Error reading cache file {filepath}: {e}")
                return None

        # 4. If not, download it
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                # Open image from bytes
                img = Image.open(BytesIO(response.content))
                
                # Save to cache for next time
                # We convert to RGB to ensure we can save as JPEG (handling potential RGBA issues)
                img.convert('RGB').save(filepath)
                
                return img
            else:
                print(f"Failed to fetch {url} - Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def _fetch_tile(self, x: int, y: int) -> Optional[Image.Image]:
        # Heuristic: Use Level9 for everything unless we know it's low res.
        tile_matrix_set = "GoogleMapsCompatible_Level9"
        
        # Override for lower res layers
        if "Temp" in self.layer_id or "Chlorophyll" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level7"
        if "DayNight" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level8"

        # Construct URL
        url = (
            f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            f"{self.layer_id}/default/{self.date_str}/{tile_matrix_set}/"
            f"{self.zoom}/{y}/{x}.jpg"
        )
        
        try:
            return utils.get_cached_image(url, cache_dir=f"{self.paths['maps_cache']}/{self.layer_id}")
        except Exception as e:
            log.error(f"Failed to fetch tile {x},{y}: {e}")
            return None

    def get_image(self) -> Image.Image:
        """Generates the stitched NASA map for video or file saving."""
        center_x, center_y = self._lat_lon_to_tile(self.lat, self.lon, self.zoom)
        
        canvas_w = self.tile_size * self.grid_size
        canvas_h = self.tile_size * self.grid_size
        stitched_map = Image.new('RGB', (canvas_w, canvas_h), (0, 0, 0))

        offset = self.grid_size // 2

        for i in range(self.grid_size):
            for j in range(self.grid_size):
                tile_x = center_x - offset + i
                tile_y = center_y - offset + j
                
                tile_img = self._fetch_tile(tile_x, tile_y)
                if tile_img:
                    stitched_map.paste(tile_img, (i * self.tile_size, j * self.tile_size))

        final_image = stitched_map.resize((self.width, self.height), Image.Resampling.LANCZOS)
        return final_image

    def draw(self) -> None:
        """Cycle through layers and pick a RANDOM CITY for each image."""
        layer_items = list(LAYERS.items()) 
        
        for i in range(self.file_count):
            # 1. Pick a Random City
            city_name, coords = random.choice(list(CITIES.items()))
            temp_lat = coords[0]
            temp_lon = coords[1]

            # 2. Select Layer Cyclically
            layer_name, layer_info = layer_items[i % len(layer_items)]
            
            # FIX: Ensure string matches "Night Lights" in your LAYERS dict
            if layer_name == "Night Lights":
                if not is_night_at_location(temp_lat, temp_lon):
                    log.info(f"Skipping {city_name} for Night Lights: It is currently daylight there.")
                    continue

            # 3. Update Class State BEFORE calling get_image
            self.lat = temp_lat
            self.lon = temp_lon
            self.layer_id = layer_info[0]
            
            # 4. Recalculate Zoom
            max_zoom = layer_info[1]
            requested_zoom = int(self.config.get('zoom', 4))
            self.zoom = min(requested_zoom, max_zoom)
            
            log.info(f"Generating: {city_name} - {layer_name} (Zoom: {self.zoom})")
            
            # 5. Generate & Save
            img = self.get_image() # This now uses the updated self.lat/lon/layer_id
            
            # Sanitized filenames
            safe_layer_name = layer_name.replace(" ", "_").replace("(", "").replace(")", "")
            safe_city_name = city_name.split(",")[0].replace(" ", "_")
            
            # Ensure the directory exists and save
            filename = f"{self.base_filename}_{i+1}_{safe_city_name}_{safe_layer_name}.jpeg"
            # Note: self.save usually handles the path joining if using a framework
            self.save(img, filename) 
            log.info(f"Saved NASA Image: {filename}")
