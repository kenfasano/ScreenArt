import os
import sys

# 1. Get the directory containing this script (e.g., .../ScreenArt/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Build the path to RasterTransformers relative to this script
TARGET_DIR = os.path.join(SCRIPT_DIR, "Transformers", "RasterTransformers")

# 3. Check where transformerDictionary.py actually is
DICT_PATH_ROOT = os.path.join(SCRIPT_DIR, "Transformers", "transformerDictionary.py")
DICT_PATH_SUB = os.path.join(TARGET_DIR, "transformerDictionary.py")

# Determine correct import based on file location
if os.path.exists(DICT_PATH_ROOT):
    IMPORT_STATEMENT = "from Transformers.transformerDictionary import"
    print(f"Found dictionary in Transformers root. Using: {IMPORT_STATEMENT}")
elif os.path.exists(DICT_PATH_SUB):
    IMPORT_STATEMENT = "from .transformerDictionary import" # Relative import is safer if inside subdir
    print(f"Found dictionary in RasterTransformers. Using: {IMPORT_STATEMENT}")
else:
    print("WARNING: transformerDictionary.py not found in expected locations.")
    print("Defaulting to Transformers root import.")
    IMPORT_STATEMENT = "from Transformers.transformerDictionary import"


def refactor_file(filepath):
    print(f"Scanning {os.path.basename(filepath)}...")
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    changes_made = False
    
    for line in lines:
        stripped = line.strip()
        
        # Match "from .transformerDictionary ..." OR "from ..transformerDictionary ..." OR "from Transformers.transformerDictionary"
        if "transformerDictionary" in stripped and "import" in stripped:
            # Check what it is importing (e.g., "transformer_ids", "transformer_styles")
            try:
                imports_part = stripped.split("import")[1]
            except IndexError:
                # Handle edge case where line might be malformed or different syntax
                 new_lines.append(line)
                 continue

            # Construct the New Import
            new_line = f"{IMPORT_STATEMENT}{imports_part}\n"
            
            # Preserve indentation if any (though usually top level)
            if line.startswith("    "): 
                new_line = "    " + new_line
            
            new_lines.append(new_line)
            changes_made = True
            print(f"  -> Fixed dictionary import: {new_line.strip()}")
        else:
            new_lines.append(line)

    if not changes_made:
        return

    # Write back
    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print(f"  -> Saved changes to {os.path.basename(filepath)}")

if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR):
        print(f"CRITICAL ERROR: Directory not found: {TARGET_DIR}")
        sys.exit(1)
    
    files = os.listdir(TARGET_DIR)
    
    for filename in files:
        if filename.endswith("Transformer.py") and filename != "base.py":
            refactor_file(os.path.join(TARGET_DIR, filename))
            
    print("Dictionary Imports Refactor Complete.")
