#!/bin/bash
echo "Running favorites.sh"
export PYTHONPATH="${PYTHONPATH}:/Users/kenfasano/Scripts"

python3.14 -m ScreenArt.main "$@" -d "/Users/kenfasano/Scripts/ScreenArt/Images/static_favorites"
rc=$?

echo "Favorites: ran ScreenArt.main. rc=$rc"
echo "Ran favorites.sh"
