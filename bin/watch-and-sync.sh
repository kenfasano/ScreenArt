#!/bin/bash
# watch-and-sync.sh — fswatch wrapper that debounces and syncs to VM
set -euo pipefail

WATCH_DIR="$HOME/Scripts/ScreenArt/Images/TransformedImages"
SYNC_SCRIPT="$HOME/Scripts/ScreenArt/bin/sync-to-vm.sh"
LOG="$HOME/Library/Logs/screenart-sync.log"

exec >> "$LOG" 2>&1
echo "=== watch-and-sync started $(date) ==="

# fswatch with --latency=2 batches events within a 2-second window.
# --one-per-batch emits one line per batch instead of one per file.
/opt/homebrew/bin/fswatch --latency=2 --one-per-batch "$WATCH_DIR" | while read -r _; do
    echo "[$(date)] change detected, syncing..."
    "$SYNC_SCRIPT" || echo "[$(date)] sync failed (exit $?)"
done
