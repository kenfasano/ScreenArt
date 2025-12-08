#!/opt/homebrew/bin/zsh

# Directories
PROJECT_PARENT_DIR="/Users/kenfasano/Scripts" 
END_AT_MIDNIGHT=1 #False

# Use 'caffeinate -imsu zsh -c "..."' to run the loop persistently
caffeinate -imsu zsh -c '
cd "$PROJECT_PARENT_DIR"
while true; do
    # --- New Logic ---
    # Get the current hour (e.g., "00", "01", ..., "23")
    # We use 10# to force base-10 interpretation, avoiding octal issues
    local hour=$(date +%H)
    
    # Check if the hour is between 00:00 and 05:59 (i.e., hour < 6)
    # This is the "past midnight" window. You can change "6" to "7"
    # if you want it to stop until 7:00 AM.
	 if [ $END_AT_MIDNIGHT ]; then
		 if (( 10#$hour < 6 )); then
			  echo "Nighttime detected (Hour: $hour). Stopping loop and releasing caffeinate."
			  # Exit the loop. This terminates the zsh script,
			  # which releases the caffeinate lock,
			  # allowing the computer to sleep normally.
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

    # Wait for 1 hour
    echo "Sleeping for 1 hour..."
    sleep 1h 
done
'
