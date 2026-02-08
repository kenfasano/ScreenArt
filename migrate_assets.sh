#!/bin/zsh

echo "📦 Starting Asset Migration to Shared Drive..."

# --- 1. Define Paths ---
# Target Directory (The Shared Drive)
TARGET_ROOT="/Volumes/Shared/Scripts/ScreenArt"
TARGET_DATA="$TARGET_ROOT/InputSources/Data"
TARGET_FONTS="$TARGET_ROOT/Assets/Fonts"

# Source Directories (Your Mac-specific paths)
SRC_LOJONG="/Users/kenfasano/Library/Mobile Documents/com~apple~CloudDocs/Scripts/ScreenArt/InputSources/Data/Lojong"
SRC_FONT="/Users/kenfasano/Library/Fonts/NotoSerifTibetan-VariableFont_wght.ttf"

# --- 2. Create Destination Folders ---
echo "📂 Creating folder structures..."
mkdir -p "$TARGET_DATA"
mkdir -p "$TARGET_FONTS"

# --- 3. Copy Lojong Data (From iCloud) ---
if [[ -d "$SRC_LOJONG" ]]; then
    echo "✅ Found iCloud Lojong data. Copying to Shared..."
    # We use cp -R (recursive) to copy the folder
    cp -R "$SRC_LOJONG" "$TARGET_DATA/"
else
    echo "⚠️  Warning: Could not find Lojong folder at: $SRC_LOJONG"
fi

# --- 4. Copy Fonts (From User Library) ---
if [[ -f "$SRC_FONT" ]]; then
    echo "✅ Found Tibetan Font. Copying to Shared Assets..."
    cp "$SRC_FONT" "$TARGET_FONTS/"
else
    echo "⚠️  Warning: Could not find font at: $SRC_FONT"
fi

echo "🎉 Migration Complete!"
echo "   -> Lojong is now in: $TARGET_DATA/Lojong"
echo "   -> Font is now in:   $TARGET_FONTS"
