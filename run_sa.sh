#!/bin/bash

# --- 1. Set Defaults ---
num_times=""
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

if [ -z "${num_times}" ]; then
    echo "Starting ScreenArt loop infinitely with ${sleep_seconds}s sleep..."
else
    echo "Starting ScreenArt loop with ${num_times} iterations and ${sleep_seconds}s sleep..."
fi

# --- 3. Run Loop ---
i=1
while true; do
    echo "-----------------------------------"
    if [ -z "${num_times}" ]; then
        echo "Run ${i} (infinite loop) - $(date)"
    else
        echo "Run ${i} of ${num_times} - $(date)"
    fi
    echo "-----------------------------------"

    # Execute your command
    cd ~/Scripts
	 source .venv/bin/activate && .venv/bin/python3 -m ScreenArt.main
	 rc=$?
	 if [[ rc -ne 0 ]]; then
		 exit 1
  	 fi
	 echo "rc=${rc}"

    # Exit if we've hit the requested number of runs
    if [ -n "${num_times}" ] && [ "${i}" -ge "${num_times}" ]; then
        break
    fi

    echo "$i${num_times:+/$num_times}: Waiting for $sleep_seconds second(s)..."
    sleep "${sleep_seconds}"
    (( i++ ))
done

if [ -n "${num_times}" ]; then
    echo "${num_times}-run cycle complete!"
fi
