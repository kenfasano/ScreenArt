import os

BASE_PATH = os.path.expanduser("~/Scripts/ScreenArt")
IMAGE_DIR = BASE_PATH + "/Images"
FAVORITES_IN = IMAGE_DIR + "/Favorites"
GENERATORS_IN = IMAGE_DIR + "/Generators"
TRANSFORMERS_OUT = IMAGE_DIR + "/TransformedImages"
REJECTED_OUT = IMAGE_DIR + "/Rejected" # Case correction based on typical Mac paths
WIKI_OUT = IMAGE_DIR + "/Generators/Wiki"
MAPS_OUT = IMAGE_DIR + "/Generators/Maps"
GOES_OUT = IMAGE_DIR + "/Generators/GOES"
NASA_CACHE = IMAGE_DIR + "/cache/nasa"
WIKI_CACHE = IMAGE_DIR + "/cache/wiki"
MENUBAR_FILE = "/Users/kenfasano/Scripts/Menubar/transformers.txt"
