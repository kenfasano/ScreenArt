#!/bin/bash

# --- 1. Set Defaults ---
num_times=24
sleep_seconds=3600

# --- 2. Parse Command Line Arguments ---
# n: (num_times), s: (sleep_seconds)
while getopts "n:s:" opt; do
  case ${opt} in
    n) num_times=${OPTARG} ;;
    s) sleep_seconds=${OPTARG} ;;
    *) echo "Usage: $0 [-n num_times] [-s sleep_seconds]" >&2
       exit 1 ;;
  esac
done

echo "Starting ScreenArt loop with ${num_times} iterations and ${sleep_seconds}s sleep..."

# --- 3. Run Loop ---
# Using (( )) for C-style loop to handle the variable num_times
for (( i=1; i<=${num_times}; i++ ))
do
    echo "-----------------------------------"
    echo "Run ${i} of ${num_times} - $(date)"
    echo "-----------------------------------"
    
    # Execute your command
    cd ~/Scripts
	 source .venv/bin/activate && .venv/bin/python3 -m ScreenArt.main
    
    # Sleep unless it's the very last run
    if [ "${i}" -lt "${num_times}" ]; then
        echo "$i/$num_times: Waiting for $sleep_seconds seconds..."
        sleep "${sleep_seconds}"
    fi
done

echo "${num_times}-run cycle complete!"
