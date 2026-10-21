"""Shared configuration for ScreenArt viewer + importer.

Layout:
- Art images live in iCloud (where ScreenArt writes them).
- Viewer code + state lives wherever this file is (typically local).
- HeartedQueue staging lives next to the code, NOT in iCloud,
  to avoid syncing temp files that get deleted within 5 minutes.
"""
from pathlib import Path

HOME = Path.home()

# Where ScreenArt writes finished images (iCloud-resident)
SCREENART_DIR = (
    HOME
    / "Scripts" 
    / "ScreenArt"
)
IMAGES_DIR = SCREENART_DIR / "Images" / "TransformedImages"

# Viewer state lives next to viewer code (wherever config.py is)
VIEWER_DIR = Path(__file__).resolve().parent
SAVED_JSON = VIEWER_DIR / "saved.json"
IMPORTED_LOG = VIEWER_DIR / ".imported"
HEARTED_QUEUE = VIEWER_DIR / "HeartedQueue"

# Photos.app
ALBUM_NAME = "ScreenArt"

# Network
HOST = "0.0.0.0"   # bind all interfaces so iPad can reach over LAN
PORT = 8080

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
