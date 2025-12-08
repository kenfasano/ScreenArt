import os
import sys

# 1. Get the directory containing this script (e.g., .../ScreenArt/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Build the path to RasterTransformers relative to this script
TARGET_DIR = os.path.join(SCRIPT_DIR, "Transformers", "RasterTransformers")

def refactor_file(filepath):
    print(f"Scanning {os.path.basename(filepath)}...")
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    imports_to_move = []
    
    # 3. Scan for imports to remove/modify
    for line in lines:
        stripped = line.strip()
        
        # FIX A: hex_to_rgb -> Absolute
        if "hex_to_rgb" in stripped and "import" in stripped:
             imports_to_move.append("        from Transformers import hex_to_rgb\n")
             continue 

        # FIX B: common -> Absolute
        if "import common" in stripped:
            imports_to_move.append("        import common\n")
            continue

        # FIX C: log -> Absolute
        if "import log" in stripped:
            imports_to_move.append("        import log\n")
            continue

        new_lines.append(line)

    if not imports_to_move:
        return

    # 4. Inject them into 'def apply'
    final_content = []
    for line in new_lines:
        final_content.append(line)
        if "def apply(self," in line:
            print(f"  -> Injecting fixed imports into 'apply'")
            final_content.extend(imports_to_move)

    # 5. Write back
    with open(filepath, "w") as f:
        f.writelines(final_content)
    print(f"  -> Saved changes to {os.path.basename(filepath)}")

if __name__ == "__main__":
    if not os.path.exists(TARGET_DIR):
        print(f"CRITICAL ERROR: Directory not found: {TARGET_DIR}")
        sys.exit(1)
    
    files = os.listdir(TARGET_DIR)
    for filename in files:
        if filename.endswith("Transformer.py") and filename != "base.py":
            refactor_file(os.path.join(TARGET_DIR, filename))
            
    print("Refactor Complete.")
