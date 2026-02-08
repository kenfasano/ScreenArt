#!/opt/homebrew/bin/zsh

HOUR=$(date +%H)

# Directories
ICLOUD="/Users/kenfasano/Library/Mobile Documents/com~apple~CloudDocs/Scripts/ScreenArt/Images"
TRANSFORMED="$ICLOUD/TransformedImages"

# The parent directory of the ScreenArt package
PROJECT_PARENT_DIR="/Users/kenfasano/Scripts" 
BASE_DIR="/Users/kenfasano/Scripts/ScreenArt" # Keep this for path building

cd "$PROJECT_PARENT_DIR"

echo "RECREATING SCREEN ART ($(date))..."

# Execute the project as a module
PYTHON="$(which python3)"
echo "$PYTHON"

# CHANGE: Added "$@" to the end to pass arguments (like -t) to the python script
$PYTHON -m ScreenArt.runScreenArtTest "$@"

rc=$?
if [[ $rc -eq 0 ]]; then
    echo "Done. Recreated ScreenArt. rc=$rc"
    exit 0
else
    echo "Failed. rc=$rc"
    exit 1
fi
