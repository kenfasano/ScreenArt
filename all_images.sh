#!/bin/bash
echo "Running all_images.sh"
export PYTHONPATH="${PYTHONPATH}:/Users/kenfasano/Scripts"

python3.15 -m ScreenArt.main "$@" 
rc=$?

echo ": ran ScreenArt.main. rc=$rc"
echo "Ran all_images.sh"
