#!/usr/bin/env zsh

DIR="/Users/kenfasano/Library/Containers/com.apple.wallpaper.agent/Data/Library/Caches/com.apple.wallpaper.caches/extension-com.apple.wallpaper.extension.image"

# Bail if the directory doesn't exist
if [[ ! -d "$DIR" ]]; then
  echo "Directory not found: $DIR" >&2
  exit 1
fi

# List *.bmp by modification time, newest first, keep the top 2, delete the rest
setopt local_options extended_glob null_glob

files=("$DIR"/*.bmp(Om))   # Om = sort by mtime, newest first

count=${#files[@]}

if (( count <= 2 )); then
  echo "Only $count bmp file(s) found — nothing to delete."
  exit 0
fi

to_delete=("${files[@]:2}")  # skip first 2 (most recent), keep the rest for deletion

echo "Deleting $((count - 2)) old bmp file(s), keeping the 2 most recent:"
for f in "${to_delete[@]}"; do
  echo "  rm -- $f"
  rm -f -- "$f"
done

echo "Done."
