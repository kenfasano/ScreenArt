import os
import hashlib
import requests
from io import BytesIO
from typing import Optional
from PIL import Image # type: ignore

# Inherit from your new base Generator
from .generator import Generator

class DrawGenerator(Generator):
    """
    A specialized Generator handling image fetching, caching, and 
    canvas manipulation utilities for downstream generators.
    """
    def __init__(self):
        # 1. Initialize Generator (which calls ScreenArt)
        super().__init__()
        
        # 2. Set up the cache directory from the config, 
        # defaulting to a 'cache' folder in your base project path.
        self.cache_dir = self.config.get("paths", {}).get("cache_dir", os.path.join(self.base_path, "cache"))

        # Ensure the cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_cached_image(self, url: str) -> Optional[Image.Image]:
        """
        Checks if an image exists in the local cache.
        If yes: loads it from disk.
        If no: downloads it, saves it to disk, then loads it.
        """
        # Create a safe filename from the URL
        hash_object = hashlib.md5(url.encode())
        filename = f"{hash_object.hexdigest()}.jpg"
        filepath = os.path.join(self.cache_dir, filename)

        # Check if file exists locally
        if os.path.exists(filepath):
            try:
                self.log.debug(f"Loaded cached image from {filepath}")
                return Image.open(filepath)
            except Exception as e:
                self.log.error(f"Error reading cache file {filepath}: {e}")
                return None

        # If not, download it
        try:
            self.log.info(f"Downloading new image to cache: {url}")
            response = requests.get(url, stream=True, timeout=10)
            
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img.convert('RGB').save(filepath)
                self.log.debug(f"Saved downloaded image to {filepath}")
                return img
            else:
                self.log.error(f"Failed to fetch {url} - Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log.error(f"Error downloading {url}: {e}")
            return None
            
    # Note: We do NOT implement run() here, we leave that to the concrete generators
