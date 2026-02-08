#!/bin/zsh
# Path to your ScreenArt output
SOURCE="/home/kenfasano/.cache/current_lock_bg.png"
# Path for SDDM
TARGET="/usr/share/sddm/themes/sugar-candy/Backgrounds/ScreenArt_Login.png"

cp "$SOURCE" "$TARGET"
chmod 644 "$TARGET"
