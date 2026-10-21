#!/opt/homebrew/bin/zsh
set -euo pipefail

OUT_DIR="$HOME/Scripts/ScreenArt/InputSources/Data/UkrainianPsalms"
mkdir -p "$OUT_DIR"

BASE_URL="https://www.htmlbible.com/ukrainian/B19C"   # verify on first run
LOG_FILE="$OUT_DIR/download_errors.log"
: > "$LOG_FILE"

download_psalm() {
	local n=$1
	local p=$(printf '%03d' "$n")
	local outfile="$OUT_DIR/psalm_${n}.html"
	local url="${BASE_URL}${p}.htm"

	echo "URL: ${url}"
	echo "Downloading Psalm $n → $outfile"

	for attempt in 1 2 3; do
		# get content
		if curl -fsSL "$url" > ${outfile}; then
			echo "✓ Downloaded Psalm $n ($url)" >> "$LOG_FILE"
			return 0
		fi
	done

	echo "❌ Failed to download Psalm $n ($url)" >> "$LOG_FILE"
	return 1
}

# Main loop
for i in $(seq 1 150); do
	download_psalm "$i" || true
done

echo
echo "✅ Done. Files saved in: $OUT_DIR"
echo "Errors (if any) in: $LOG_FILE"
