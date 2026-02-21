from .drawGenerator import DrawGenerator
from PIL import Image
from astral import LocationInfo
from astral.sun import sun           
from datetime import datetime, timedelta
from typing import Optional, Tuple
import math
import os
import pytz                          
import random

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

class NasaMapGenerator(DrawGenerator):
    def __init__(self):
        super().__init__()
        
        self.width = int(self.config.get("width", 1920))
        self.height = int(self.config.get("height", 1080))
        self.file_count = int(self.config.get("file_count", 1))
        self.base_filename = "nasa_earth"
        
        self.grid_size = 3
        self.tile_size = 256
        self.zoom = 4
        self.lat = 0.0
        self.lon = 0.0
        self.layer_id = "VIIRS_SNPP_CorrectedReflectance_TrueColor"
        
        today = datetime.today()
        self.date_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    def _is_night_at_location(self, lat: float, lon: float) -> bool:
        now_utc = datetime.now(pytz.utc)
        city = LocationInfo("Target City", "Region", "UTC", lat, lon)
        try:
            s = sun(city.observer, date=now_utc, tzinfo=pytz.utc)
            if now_utc < s['sunrise'] or now_utc > s['sunset']:
                return True
            return False
        except Exception as e:
            self.log.error(f"Astral calculation error: {e}")
            return False

    def _lat_lon_to_tile(self, lat: float, lon: float, zoom: int) -> Tuple[int, int]:
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
        return xtile, ytile

    def _fetch_tile(self, x: int, y: int) -> Optional[Image.Image]:
        tile_matrix_set = "GoogleMapsCompatible_Level9"
        if "Temp" in self.layer_id or "Chlorophyll" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level7"
        if "DayNight" in self.layer_id:
             tile_matrix_set = "GoogleMapsCompatible_Level8"

        url = (
            f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/"
            f"{self.layer_id}/default/{self.date_str}/{tile_matrix_set}/"
            f"{self.zoom}/{y}/{x}.jpg"
        )
        
        try:
            # Safely create a cache subdirectory for this layer
            layer_cache = os.path.join(self.cache_dir, self.layer_id)
            return self.get_cached_image(url, cache_dir=layer_cache)
        except Exception as e:
            self.log.error(f"Failed to fetch tile {x},{y}: {e}")
            return None

    def get_image(self) -> Image.Image:
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

        return stitched_map.resize((self.width, self.height), Image.Resampling.LANCZOS)

    def run(self, *args, **kwargs) -> None:
        out_dir = os.path.join(self.config["paths"]["generators_in"], "maps")
        os.makedirs(out_dir, exist_ok=True)
        
        layer_items = list(LAYERS.items()) 
        
        for i in range(self.file_count):
            city_name, coords = random.choice(list(CITIES.items()))
            temp_lat, temp_lon = coords[0], coords[1]
            layer_name, layer_info = layer_items[i % len(layer_items)]
            
            if layer_name == "Night Lights" and not self._is_night_at_location(temp_lat, temp_lon):
                continue

            self.lat = temp_lat
            self.lon = temp_lon
            self.layer_id = layer_info[0]
            
            max_zoom = layer_info[1]
            requested_zoom = int(self.config.get('zoom', 4))
            self.zoom = min(requested_zoom, max_zoom)
            
            img = self.get_image() 
            
            safe_layer_name = layer_name.replace(" ", "_").replace("(", "").replace(")", "")
            safe_city_name = city_name.split(",")[0].replace(" ", "_")
            filename = os.path.join(out_dir, f"{self.base_filename}_{i+1}_{safe_city_name}_{safe_layer_name}.jpeg")
            
            try:
                img.save(filename)
                self.log.info(f"Saved NASA Map Image: {filename}")
            except Exception as e:
                self.log.error(f"Failed to save {filename}: {e}")
