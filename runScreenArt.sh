#!/usr/bin/env zsh

# 1. Dynamic Path Detection
SCRIPT_DIR=${0:a:h}            # .../Scripts/ScreenArt
PROJECT_PARENT_DIR=${SCRIPT_DIR:h} # .../Scripts (Where the venvs live!)

echo "📂 Script Location: $SCRIPT_DIR"
echo "📂 Venv Location:   $PROJECT_PARENT_DIR"

# 2. Detect OS and Define Python Path
OS_TYPE=$(uname)

if [[ "$OS_TYPE" == "Darwin" ]]; then
    # --- macOS Configuration ---
    # Venv is on the Shared Drive (sibling to ScreenArt folder)
    VENV_NAME=".venv_mac"
    PYTHON_EXEC="$PROJECT_PARENT_DIR/$VENV_NAME/bin/python"

elif [[ "$OS_TYPE" == "Linux" ]]; then
    # --- Linux Configuration ---
    # Venv is in the User's Home Directory (Local) to avoid symlink errors
    # We look for it at ~/.screenart_venv
    PYTHON_EXEC="$HOME/.venv_linux/bin/python"

else
    echo "❌ Unknown OS: $OS_TYPE"
    exit 1
fi

# 3. Sanity Check
if [[ ! -f "$PYTHON_EXEC" ]]; then
    echo "❌ Critical Error: Python executable not found at:"
    echo "   $PYTHON_EXEC"
    if [[ "$OS_TYPE" == "Linux" ]]; then
        echo "   -> On Linux, did you run: python3 -m venv ~/.screenart_venv ?"
    else
        echo "   -> On Mac, did you create the .venv_mac in Scripts/ ?"
    fi
    exit 1
fi
# Sanity Check: Does this python exist?
if [[ ! -f "$PYTHON_EXEC" ]]; then
    echo "❌ Critical Error: Python executable not found at:"
    echo "   $PYTHON_EXEC"
    echo "   Please check that '$VENV_NAME' exists in $PROJECT_PARENT_DIR"
    exit 1
fi

# 4. Execute
# We cd to Scripts/ so that 'python -m ScreenArt...' works correctly
cd "$PROJECT_PARENT_DIR"
echo "🚀 Launching with: $PYTHON_EXEC"

# exec replaces the shell process with python
"$PYTHON_EXEC" -m ScreenArt.runScreenArt

if [[ $? -eq 0 ]]; then
    IMAGE_DIR="/home/kenfasano/Shared/Scripts/ScreenArt"
    CACHE_LINK="/home/kenfasano/.cache/current_lock_bg.png"
    
    RANDOM_IMAGE=$(find "$IMAGE_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" \) | shuf -n 1)
    
    if [[ -f "$RANDOM_IMAGE" ]]; then
        ln -sf "$RANDOM_IMAGE" "$CACHE_LINK"
		  ./sync_login_bg.sh
        # Optional: Send a signal to hyprlock if it's currently running
        pkill -USR1 hyprlock 
        echo "🔒 Lock screen visuals refreshed."
    fi
fi
