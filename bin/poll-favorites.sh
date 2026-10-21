#!/bin/bash
# poll-favorites.sh — fetch hearted favorites from VM, import to Photos.app
set -euo pipefail

VM_HOST="archbox"
VM_BASE="http://localhost:8080"
ALBUM="ScreenArt"
WORK_DIR="$HOME/Scripts/ScreenArt/Images/PhotosImportQueue"
IMPORTED_LOG="$WORK_DIR/.imported"
LOG="$HOME/Library/Logs/screenart-poll.log"

exec >> "$LOG" 2>&1
echo "=== poll-favorites started $(date) ==="

mkdir -p "$WORK_DIR"
touch "$IMPORTED_LOG"

# Fetch saved list
SAVED_JSON=$(curl -fsS "$VM_BASE/cgi-bin/screenart.sh?action=list" || echo "[]")
echo "[$(date)] saved.json: $SAVED_JSON"

FILES=$(echo "$SAVED_JSON" | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin)))' 2>/dev/null || true)

if [[ -z "$FILES" ]]; then
    echo "[$(date)] nothing to do"
    exit 0
fi

while IFS= read -r FILE; do
    [[ -z "$FILE" ]] && continue

    # Skip if we've already imported this filename
    if grep -qxF "$FILE" "$IMPORTED_LOG"; then
        echo "[$(date)] already imported $FILE — calling clear and skipping"
        CLEAR_RESP=$(curl -fsS "$VM_BASE/cgi-bin/screenart.sh?action=clear&file=$FILE" || echo "CURL_FAILED")
        echo "[$(date)] clear response: $CLEAR_RESP"
        continue
    fi

    echo "[$(date)] processing: $FILE"

    LOCAL="$WORK_DIR/$FILE"
    if ! scp -q "$VM_HOST:/srv/http/saved-favorites/$FILE" "$LOCAL"; then
        echo "[$(date)] scp failed for $FILE, skipping"
        continue
    fi

    if osascript <<EOF
tell application "Photos"
    if not (exists album "$ALBUM") then
        make new album named "$ALBUM"
    end if
    import {POSIX file "$LOCAL"} into album "$ALBUM" skip check duplicates yes
end tell
EOF
    then
        echo "[$(date)] imported $FILE"
        echo "$FILE" >> "$IMPORTED_LOG"
        CLEAR_RESP=$(curl -fsS "$VM_BASE/cgi-bin/screenart.sh?action=clear&file=$FILE" || echo "CURL_FAILED")
        echo "[$(date)] clear response: $CLEAR_RESP"
        rm -f "$LOCAL"
    else
        echo "[$(date)] osascript failed for $FILE, leaving on VM"
    fi
done <<< "$FILES"

echo "[$(date)] done"
