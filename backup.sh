#!/bin/bash

# Define source and destination
SRC="."
DEST="/Users/kenfasano/Library/Mobile Documents/com~apple~CloudDocs/Scripts/ScreenArt"

# Create the destination directory if it doesn't exist
mkdir -p "$DEST"

# Run rsync to copy only newer .py, .sh, and .conf files
rsync -avu --include='*/' --include='*.py' --include='*.sh' --include='*.conf' --exclude='*' "$SRC/" "$DEST/" "Images/" "Logs/"
