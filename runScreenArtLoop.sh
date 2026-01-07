#!/opt/homebrew/bin/zsh

# Directories
PROJECT_PARENT_DIR="/Users/kenfasano/Scripts" 
END_AT_MIDNIGHT=1

# Export the directory so the inner 'caffeinate' shell can see it
export PROJECT_PARENT_DIR

# Use 'caffeinate -imsu zsh -c "..."' to run the loop persistently
caffeinate -imsu zsh -c '
# Ensure we are in the correct directory
cd "$PROJECT_PARENT_DIR" || exit 1

while true; do
    # --- Time Check Logic ---
    # Get the current hour (e.g., "00", "01", ..., "23")
    hour=$(date +%H)
    
    # Check if the hour is between 00:00 and 05:59
    if [[ -n "$END_AT_MIDNIGHT" ]]; then
         if (( 10#$hour < 6 )); then
              echo "Nighttime detected (Hour: $hour). Stopping loop and releasing caffeinate."
              exit 0
         fi
    fi

    # --- Run Generator ---
    echo "Running ScreenArt/runScreenArt.sh..."
    ScreenArt/runScreenArt.sh
    rc=$?

    # Check return code
    if [[ $rc -ne 0 ]]; then
        echo "runScreenArt.sh failed with rc=$rc. Exiting loop."
        exit 1
    fi

    # --- Random Sleep Logic (60 to 120 minutes) ---
    # We use Python to generate a random integer between 3600 (60m) and 7200 (120m) seconds.
    SLEEP_SEC=$(python3 -c "import random; print(int(random.uniform(3600, 7200)))")
    
    # Calculate minutes just for the log message
    SLEEP_MIN=$(echo "scale=2; $SLEEP_SEC / 60" | bc)
    
    echo "Sleeping for $SLEEP_SEC seconds (~$SLEEP_MIN minutes)..."
    sleep $SLEEP_SEC
done
'
