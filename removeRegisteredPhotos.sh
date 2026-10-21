#!/bin/zsh
#
# remove_wallpaper_folder.sh
#
# Deletes a single entry (by index) from DSKDesktopPrefPane:UserFolderPaths
# in ~/Library/Preferences/com.apple.systempreferences.plist, if that index
# is a valid, present entry in the array. Otherwise prints an error and exits.
#
# Usage:
#   ./remove_wallpaper_folder.sh <index>
#
# Example:
#   ./remove_wallpaper_folder.sh 2

set -o pipefail

PLIST="$HOME/Library/Preferences/com.apple.systempreferences.plist"
KEY=":DSKDesktopPrefPane:UserFolderPaths"

# --- Validate arguments ---
if [[ $# -ne 1 ]]; then
    echo "Error: expected exactly one argument (the index to delete)." >&2
    echo "Usage: $0 <index>" >&2
    exit 1
fi

INDEX="$1"

if ! [[ "$INDEX" =~ ^[0-9]+$ ]]; then
    echo "Error: '$INDEX' is not a valid non-negative integer index." >&2
    exit 1
fi

# --- Validate plist exists ---
if [[ ! -f "$PLIST" ]]; then
    echo "Error: plist not found at $PLIST" >&2
    exit 1
fi

# --- Validate the key/array exists ---
ARRAY_DUMP=$(/usr/libexec/PlistBuddy -c "Print $KEY" "$PLIST" 2>&1)
if [[ $? -ne 0 ]]; then
    echo "Error: could not read $KEY from plist (it may not exist)." >&2
    echo "Details: $ARRAY_DUMP" >&2
    exit 1
fi

# --- Validate the specific index exists ---
ENTRY=$(/usr/libexec/PlistBuddy -c "Print ${KEY}:${INDEX}" "$PLIST" 2>&1)
if [[ $? -ne 0 ]]; then
    echo "Error: index $INDEX is not present in $KEY." >&2
    echo "Current entries:" >&2
    echo "$ARRAY_DUMP" >&2
    exit 1
fi

echo "About to delete index $INDEX: $ENTRY"

# --- Backup before editing ---
BACKUP="${PLIST}.bak.$(date +%Y%m%d%H%M%S)"
cp "$PLIST" "$BACKUP"
echo "Backup saved to $BACKUP"

# --- Delete the entry ---
DELETE_OUTPUT=$(/usr/libexec/PlistBuddy -c "Delete ${KEY}:${INDEX}" "$PLIST" 2>&1)
if [[ $? -ne 0 ]]; then
    echo "Error: failed to delete index $INDEX." >&2
    echo "Details: $DELETE_OUTPUT" >&2
    exit 1
fi

echo "Deleted index $INDEX from $KEY."

# --- Flush prefs cache so System Settings picks up the change ---
killall cfprefsd 2>/dev/null

echo "Done. Reopen System Settings > Wallpaper to confirm."

