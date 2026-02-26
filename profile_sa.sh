#!/bin/bash

# Define paths
APP_DIR="$HOME/Scripts/ScreenArt"
VENV_PYTHON="$HOME/Scripts/.venv/bin/python3"
STATS_FILE="screenart.prof"

echo "Running ScreenArt with cProfile..."
PROFILES_DIR="$APP_DIR/profiles"
mkdir -p "$PROFILES_DIR"
TIMESTAMP=$(date +%y-%m-%d-%H:%M)
STATS_FILE="$PROFILES_DIR/screenart-$TIMESTAMP.prof"

# Navigate to the parent directory to match your main.py import structure
cd ~/Scripts

# Run the app through cProfile
# -m cProfile: Runs the profiler
# -o: Saves the output to a file
$VENV_PYTHON -m cProfile -o $STATS_FILE -m ScreenArt.main

# Check if the stats file was created and launch SnakeViz
if [ -f "$STATS_FILE" ]; then
    echo "Profiling complete. Launching browser..."
    $HOME/Scripts/.venv/bin/snakeviz $STATS_FILE
else
    echo "Error: Profiling file was not generated."
fi
