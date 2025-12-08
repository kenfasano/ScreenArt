import os
import shutil
import re

# CONFIGURATION
SOURCE_DIR = "ScreenArt/Transformers"
DEST_DIR = "ScreenArt/Transformers/RasterTransformers"
OLD_PARENT_CLASS = "ImageTransformer"
NEW_PARENT_CLASS = "RasterTransformer"

# List your 19 files here (or use os.listdir to grab them all)
FILES_TO_MOVE = [
    "anamorphicTransformer.py",
    "colormapTransformer.py",
    "dataMoshTransformer.py",
    "duotoneTransformer.py",
    "fisheyeTransformer.py",
    "fluidWarpTransformer.py",
    "fractalWarpTransformer.py",
    "glitchWarpTransformer.py",
    "halftoneTransformer.py",
    "meltMorphTransformer.py",
    "nullTransformer.py",
    "posterizationTransformer.py",
    "radialWarpTransformer.py",
    "swirlWarpTransformer.py",
    "thermalImagingTransformer.py",
    "threeDExtrusionTransformer.py",
    "tritoneTransformer.py",
    "watercolorTransformer.py",
    "xrayTransformer.py"
]

def refactor_file(filename):
    source_path = os.path.join(SOURCE_DIR, filename)
    dest_path = os.path.join(DEST_DIR, filename)

    if not os.path.exists(source_path):
        print(f"Skipping {filename} (Not found)")
        return

    with open(source_path, "r") as f:
        content = f.read()

    # 1. Update the Class Definition
    # Replaces "class AnamorphicTransformer(ImageTransformer):"
    # with "class AnamorphicTransformer(RasterTransformer):"
    content = content.replace(f"({OLD_PARENT_CLASS})", f"({NEW_PARENT_CLASS})")

    # 2. Update the Base Import
    # Removes: from .base_transformer import ImageTransformer
    # Adds:    from .base import RasterTransformer
    content = re.sub(
        r"from\s+\.base_transformer\s+import\s+ImageTransformer", 
        "from .base import RasterTransformer", 
        content
    )

    # 3. Fix Relative Imports (The Tricky Part)
    # Because we moved down one folder, we must add a dot to relative imports.
    
    # "from . import hex_to_rgb"  -> "from .. import hex_to_rgb"
    content = re.sub(r"from\s+\.\s+import", "from .. import", content)
    
    # "from .. import common"     -> "from ... import common"
    content = re.sub(r"from\s+\.\.\s+import", "from ... import", content)

    # 4. Write to new location
    with open(dest_path, "w") as f:
        f.write(content)
    
    print(f"Processed and moved: {filename}")

    # Optional: Delete old file after verification
    # os.remove(source_path)

if __name__ == "__main__":
    # Ensure destination exists
    os.makedirs(DEST_DIR, exist_ok=True)
    
    # Create an empty __init__.py if it doesn't exist
    open(os.path.join(DEST_DIR, "__init__.py"), 'a').close()

    print("Starting Refactor...")
    for file in FILES_TO_MOVE:
        refactor_file(file)
    print("Done! Verify files in " + DEST_DIR)
