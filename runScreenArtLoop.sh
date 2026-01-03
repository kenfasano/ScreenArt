#!/opt/homebrew/bin/zsh

# Directories
PROJECT_PARENT_DIR="/Users/kenfasano/Scripts" 
END_AT_MIDNIGHT=1 #False

# Get sleep duration from first argument, default to "30m" if not provided
SLEEP_DURATION="${1:-60m}"

# Use 'caffeinate -imsu zsh -c "..."' to run the loop persistently
caffeinate -imsu zsh -c '
cd "$PROJECT_PARENT_DIR"
while true; do
    # --- New Logic ---
    # Get the current hour (e.g., "00", "01", ..., "23")
    local hour=$(date +%H)
    
    # Check if the hour is between 00:00 and 05:59
	 if [ $END_AT_MIDNIGHT ]; then
		 if (( 10#$hour < 6 )); then
			  echo "Nighttime detected (Hour: $hour). Stopping loop and releasing caffeinate."
			  exit 0
		 fi
 	 fi
    # --- End New Logic ---

    # Original script logic
    echo "Running ScreenArt/runScreenArt.sh..."
    ScreenArt/runScreenArt.sh
    rc=$?

    # Check return code and exit if failure (optional)
    if [[ $rc -eq 0 ]]; then
        echo "runScreenArt.sh succeeded with rc=$rc."
    else
        echo "runScreenArt.sh failed with rc=$rc. Exiting loop."
        exit 1
    fi

    # Wait for the specified duration (injected from outer variable)
    echo "Sleeping for '"$SLEEP_DURATION"'..."
    sleep '"$SLEEP_DURATION"'
done
'
