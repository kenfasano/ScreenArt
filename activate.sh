if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    source ~/.venv_linux/bin/activate
elif [[ "$OSTYPE" == "darwin"* ]]; then
    source ~/.venv_mac/bin/activate
fi
export PYTHONPATH="$HOME/Scripts/Libs:$PYTHONPATH"
echo "ScreenArt Environment Active: Libs added to PYTHONPATH"

