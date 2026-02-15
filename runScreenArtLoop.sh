#!/usr/bin/env zsh

# Get the directory where THIS script lives (Shared/Scripts/ScreenArt)
SCRIPT_DIR=${0:a:h}
# Get the parent (Shared/Scripts)
PROJECT_PARENT_DIR=${SCRIPT_DIR:h}

# Force execution to stay on the Shared drive
cd "$PROJECT_PARENT_DIR"

while true; do
    echo "Running ScreenArt/runScreenArt.sh..."
    # Call the script using relative path
    ./ScreenArt/runScreenArt.sh
    
    rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "runScreenArt.sh failed with rc=$rc. Exiting loop."
        break
    fi
    sleep 10
done
