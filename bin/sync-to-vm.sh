#!/bin/bash
# sync-to-vm.sh — mirror Mac TransformedImages to Arch VM gallery
set -euo pipefail

SRC="$HOME/Scripts/ScreenArt/Images/TransformedImages/"
DST="archbox:/srv/http/recent/"

# Dry run if invoked with -n
DRY=""
if [[ "${1:-}" == "-n" ]]; then
    DRY="-n"
    echo "DRY RUN — no changes will be made"
fi

rsync -av $DRY --delete \
    --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
    --exclude='.*' \
    --exclude='index.html' \
    --exclude='.regen.sh' \
    "$SRC" "$DST"
