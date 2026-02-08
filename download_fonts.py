import os
import requests

# Define your fonts directory
FONT_DIR = os.path.expanduser("~/GoogleDrive/Scripts/ScreenArt/Fonts")
SUP_DIR = os.path.join(FONT_DIR, "Supplemental")

# Ensure directories exist
os.makedirs(FONT_DIR, exist_ok=True)
os.makedirs(SUP_DIR, exist_ok=True)

# Font URLs (Direct download links)
fonts = {
    "English": {
        "url": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab[wght].ttf",
        "path": os.path.join(SUP_DIR, "RobotoSlab-Regular.ttf"),
        "name": "RobotoSlab-Regular.ttf"
    },
    "Hebrew": {
        # Heebo is excellent for Hebrew
        "url": "https://github.com/google/fonts/raw/main/ofl/heebo/Heebo[wght].ttf",
        "path": os.path.join(FONT_DIR, "Heebo-VariableFont_wght.ttf"),
        "name": "Heebo-VariableFont_wght.ttf"
    },
    "Tibetan": {
        "url": "https://github.com/google/fonts/raw/main/ofl/notoseriftibetan/NotoSerifTibetan[wght].ttf",
        "path": os.path.join(FONT_DIR, "NotoSerifTibetan-VariableFont_wght.ttf"),
        "name": "NotoSerifTibetan-VariableFont_wght.ttf"
    }
}

print(f"Downloading fonts to: {FONT_DIR}...")

for lang, data in fonts.items():
    print(f"Downloading {lang} font ({data['name']})...")
    try:
        response = requests.get(data['url'], allow_redirects=True)
        if response.status_code == 200:
            with open(data['path'], 'wb') as f:
                f.write(response.content)
            print(f"✅ Saved: {data['path']}")
        else:
            print(f"❌ Failed to download {lang}: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Error downloading {lang}: {e}")

print("\nDone! Now update your text.py with these filenames:")
print(f"English:  'Supplemental/{fonts['English']['name']}'")
print(f"Hebrew:   '{fonts['Hebrew']['name']}'")
print(f"Tibetan:  '{fonts['Tibetan']['name']}'")
