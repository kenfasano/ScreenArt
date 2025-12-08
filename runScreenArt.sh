#!/opt/homebrew/bin/zsh

HOUR=$(date +%H)

HOUR=$(date +%H)

# Directories
ICLOUD="/Users/kenfasano/Library/Mobile Documents/com~apple~CloudDocs/Scripts/ScreenArt/Images"
TRANSFORMED="$ICLOUD/TransformedImages"

# The parent directory of the ScreenArt package
PROJECT_PARENT_DIR="/Users/kenfasano/Scripts" 
BASE_DIR="/Users/kenfasano/Scripts/ScreenArt" # Keep this for path building

cd "$PROJECT_PARENT_DIR"

echo "RECREATING SCREEN ART ($(date))..."
# ... (rest of the directory cleanup code) ...

# Execute the project as a module (e.g., assuming the main entry point is 'run.py' or 'ScreenArt')
# Since the traceback shows the final execution hits run.py, we'll execute that:
PYTHON="$(which python3)"
echo "$PYTHON"
$PYTHON -m ScreenArt.runScreenArt

rc=$?
if [[ $rc -eq 0 ]]; then
    echo "Done. Recreated ScreenArt. rc=$rc"
    exit 0
else
    echo "Failed. rc=$rc"
    exit 1
fi
