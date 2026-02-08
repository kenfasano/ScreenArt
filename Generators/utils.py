import os
import hashlib
import requests
from io import BytesIO
from PIL import Image # type: ignore
from typing import Optional

def get_cached_image(url: str, cache_dir: str = "cache") -> Optional[Image.Image]:
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
