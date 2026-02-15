import math
import random
import datetime
from typing import Tuple, Optional
from PIL import Image  # type: ignore
from . import drawGenerator
from .. import log
from . import utils
from datetime import datetime, timedelta
import pytz                          
from astral.sun import sun           
from astral import LocationInfo
from typing import Any # Import Any for flexible dicts

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

    def _fetch_tile(self, x: int, y: int) -> Optional[Image.Image]:
        # Heuristic: Use Level9 for everything unless we know it's low res.
        tile_matrix_set = "GoogleMapsCompatible_Level9"
        
        # Override for lower res layers
        if "Temp" in self.layer_id or "Chlorophyll" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level7"
        if "DayNight" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level8"

        url = (
            f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            f"{self.layer_id}/default/{self.date_str}/{tile_matrix_set}/"
            f"{self.zoom}/{y}/{x}.jpg"
        )
        
        return utils.get_cached_image(url, cache_dir=f"{self.paths["nasa_cache"]}/{self.layer_id}")

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
        layer_items = list(LAYERS.items()) # List of (Name, (ID, MaxZoom))
        
        for i in range(self.file_count):
            # 1. Pick a Random City
            city_name, coords = random.choice(list(CITIES.items()))
            self.lat = coords[0]
            self.lon = coords[1]

            # 2. Select Layer Cyclically
            layer_name, layer_info = layer_items[i % len(layer_items)]
            
            if layer_name == "Night_Lights":
                if not is_night_at_location(self.lat, self.lon):
                    print(f"Skipping {layer_name}: It is currently daylight at this location.")
                    continue

            log.info(f"Rendering {layer_name}: It is night.")
            # Render image
            # 3. Update Class State
            self.layer_id = layer_info[0]
            
            # 4. Recalculate Zoom
            max_zoom = layer_info[1]
            requested_zoom = int(self.config.get('zoom', 4))
            self.zoom = min(requested_zoom, max_zoom)
            
            log.info(f"Generating: {city_name} - {layer_name} (Zoom: {self.zoom})")
            
            # 5. Generate & Save
            img = self.get_image()
            
            # Sanitized filenames
            safe_layer_name = layer_name.replace(" ", "_").replace("(", "").replace(")", "")
            safe_city_name = city_name.split(",")[0].replace(" ", "_") # "New York, USA" -> "New_York"
            
            filename = f"{self.paths["maps_out"]}/{self.base_filename}_{i+1}_{safe_city_name}_{safe_layer_name}.jpeg"
            
            img.save(filename, 'JPEG')
            log.info(f"Saved NASA Image: {filename}")
