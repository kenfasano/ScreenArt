#!/bin/bash
echo "Running white_tara.sh"
export PYTHONPATH="${PYTHONPATH}:/Users/kenfasano/Scripts"

python3.14 -m ScreenArt.main -n 1 -f "/Users/kenfasano/Scripts/ScreenArt/Images/static_favorites/white_tara.jpg"
rc=$?

echo "White_tara: ran ScreenArt.main. rc=$rc"
echo "Ran white_tara.sh"
