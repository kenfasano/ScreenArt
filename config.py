import sys
import platform
from pathlib import Path

# --- 1. Dynamic Root Detection ---
# Use .absolute() instead of .resolve() to preserve symlinks/mount structures
PROJECT_ROOT = Path(__file__).parent.absolute()

# --- 2. Path Definitions ---

# VOL_PATH: The root of the ScreenArt project
VOL_PATH = str(PROJECT_ROOT) + "/"

# BASE_PATH: ERROR FIX -> Set this to Root, not Data.
# The scripts (Bible/Lojong) already append "InputSources/Data", so we just need the root here.
BASE_PATH = str(PROJECT_ROOT) + "/"

# Favorites/Generators/etc
FAVORITES_IN = str(PROJECT_ROOT / "Images/Favorites")
GENERATORS_IN = str(PROJECT_ROOT / "Images/Generators")
TRANSFORMERS_OUT = str(PROJECT_ROOT / "Images/TransformedImages")
REJECTED_OUT = str(PROJECT_ROOT / "Images/Rejected")
WIKI_OUT = str(PROJECT_ROOT / "Images/Generators/Wiki")
MAPS_OUT = str(PROJECT_ROOT / "Images/Generators/Maps")
GOES_OUT = str(PROJECT_ROOT / "Images/Generators/GOES")

# Caches
NASA_CACHE = str(PROJECT_ROOT / "cache/nasa")
WIKI_CACHE = str(PROJECT_ROOT / "cache/wiki")

MENUBAR_FILE = str(PROJECT_ROOT / "Menubar/transformers.txt")

# --# --- 3. Font Logic ---
FONTS_DIR = PROJECT_ROOT / "Fonts" 

def get_font_path(font_name):
    """
    Returns the path to a font file. 
    Checks local Fonts folder first, then system fallback.
    """
    # Remove leading slashes to prevent pathlib from treating it as absolute
    clean_name = font_name.lstrip("/") 
    
    local_font = FONTS_DIR / clean_name
    
    if local_font.exists():
        return str(local_font)

    # Fallbacks...
    if platform.system() == "Darwin":
        return f"/Users/{Path.home().name}/Library/Fonts/{clean_name}"
    elif platform.system() == "Linux":
        # Common linux font locations
        linux_paths = [
            f"/usr/share/fonts/{clean_name}",
            f"/usr/share/fonts/truetype/{clean_name}",
            f"{Path.home()}/.local/share/fonts/{clean_name}"
        ]
        for p in linux_paths:
            if Path(p).exists():
                return p
    
    return str(local_font) # Return the local path even if missing, so the error log shows the correct path we tried
