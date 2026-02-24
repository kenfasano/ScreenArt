#!/bin/bash

echo "Starting 24-hour ScreenArt loop..."

# Loop exactly 24 times
for i in {1..24}
do
    echo "-----------------------------------"
    echo "Run $i of 24 - $(date)"
    echo "-----------------------------------"
    
    # Execute your command
	 cd ~/Scripts/ScreenArt && ./activate.sh && cd .. && ~/Scripts/.venv/bin/python3 -m ScreenArt.main
    
    # Sleep for 3600 seconds (1 hour) unless it's the very last run
    if [ $i -lt 24 ]; then
        echo "Waiting for 1 hour..."
        sleep 3600
    fi
done

echo "24-hour cycle complete!"
