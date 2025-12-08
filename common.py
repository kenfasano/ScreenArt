import numpy as np #type: ignore
import os
import re
import shutil
import urllib.parse
import log
from PIL import Image #type: ignore
from config import (
    BASE_PATH,
    FAVORITES_IN,
    INPUT_SOURCES_IN,
    TRANSFORMERS_OUT,
    REJECTED_OUT,
    MENUBAR_FILE
)

# --- REGEX FIX ---
# Changed from r'px[-_ ]+' to r'\d*px[-_ ]+' to capture the number (500) as well
PATTERN_PX = r'\d*px[-_ ]+'
PATTERN_RESOLUTION = r'\d+x\d+'
PATTERN_NUMBERS = r'\d+(?!_)'
PATTERN_SPACES = r'\s+'
PATTERN_TWO_DASHES = r'[_-]{2,}'
PATTERN_FINAL_DASH = r'-+[a-zA-Z0-9]+$'
MAX_OUT_FILE_NAME_LENGTH = 25

# --- NEW GRADING FUNCTIONS ---

def calculate_batch_grade(accepted: int, rejected: int) -> tuple[str, str]:
    """
    Calculates Grade and Ratio for the CSV report (Batch Success Rate).
    Returns (Grade Letter, Ratio String)
    """
    total = accepted + rejected
    if total == 0:
        return "F", "0.00"
    
    # Ratio: Accepted / Rejected
    if rejected == 0:
        ratio_val = float(accepted)
    else:
        ratio_val = accepted / rejected
        
    ratio_str = f"{ratio_val:.2f}"

    # Grading based on Acceptance Rate
    rate = accepted / total
    
    if rate >= 0.90: 
        grade = "A"
    elif rate >= 0.75: 
        grade = "B"
    elif rate >= 0.50: 
        grade = "C"
    else: 
        grade = "F"

    return grade, ratio_str

def calculate_image_quality_grade(dominance_percent: float, rejection_threshold: float) -> str:
    """
    Calculates a grade for a specific image based on hue dominance.
    Used for the filename prefix.
    """
    if dominance_percent > rejection_threshold:
        return "F"
    
    # Define tiers based on how far away we are from the rejection threshold
    # Example: If threshold is 75.0
    # A: < 50% (Very balanced)
    # B: 50% - 60% (Okay)
    # C: 60% - 75% (Borderline)
    
    if dominance_percent < 50.0:
        return "A"
    elif dominance_percent < 60.0:
        return "B"
    else:
        return "C"

# --- END NEW GRADING FUNCTIONS ---

def get_config(config_dict: dict, name: str) -> dict | None:
    config = config_dict.get(name, None)
    if not config:
        log.error(f"No config found for {name}")
    return config

def format_file_size(file_path: str) -> str:
    """Return the size of the file in a human-readable format."""
    size_bytes = os.path.getsize(file_path)
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    index = 0
    while size_bytes >= 1024 and index < len(units) - 1:
        size_bytes /= 1024.0
        index += 1
    return f"{size_bytes:.2f} {units[index]}"

def count_colors(path: str) -> int:
    image = Image.open(path)
    image_array = np.array(image)
    pixels = image_array.reshape(-1, image_array.shape[-1])
    unique_colors = np.unique(pixels, axis=0)
    return len(unique_colors)

def count_colors_array(image_array: np.ndarray) -> int:
    pixels = image_array.reshape(-1, image_array.shape[-1])
    unique_colors = np.unique(pixels, axis=0)
    return len(unique_colors)

def fix_file_name(file_name: str) -> str:
    file_name = urllib.parse.unquote(file_name)
    file_name = re.sub(PATTERN_PX, '', file_name)
    file_name = re.sub(PATTERN_RESOLUTION, '', file_name)
    file_name = re.sub(PATTERN_TWO_DASHES, '', file_name)
    file_name = re.sub(PATTERN_SPACES, '', file_name)
    file_name = re.sub(PATTERN_FINAL_DASH, '', file_name)

    if len(file_name) > MAX_OUT_FILE_NAME_LENGTH:
        file_name = file_name[:MAX_OUT_FILE_NAME_LENGTH - 1]

    return re.sub(r'[^\w\.]', '', file_name)

def write_response_to_file(response, path) -> bool:
    try:
        image = response.raw
        with open(path, "wb") as f:
            shutil.copyfileobj(image, f)
            return True
    except OSError as e:
        return log.error(f"OSError {e}")

def convert_png_to_jpeg(png_path, jpeg_path):
    try:
        with Image.open(png_path) as img:
            rgb_img = img.convert('RGB')
            rgb_img.save(jpeg_path, 'JPEG')
    except FileNotFoundError:
        log.error(f"Error: The file at '{png_path}' was not found.")
    except Exception as e:
        log.error(f"An error occurred: {e}")

def exclude(config: dict, capability: str) -> bool:
    return capability in config.get("exclude", [])
