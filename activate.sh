#!/bin/zsh
OS="$(uname)"

if [[ "$OS" == "Linux" ]]; then
    # Adjust this path to match your Fedora setup
    BASE_PATH="$HOME/Shared/Scripts"
    VENV_PATH="$HOME/.venv_linux/bin/activate"
elif [[ "$OS" == "Darwin" ]]; then
    # macOS specific path with "My Drive"
    BASE_PATH="$HOME/Scripts/ScreenArt"
    VENV_PATH="$HOME/Scripts/.venv/bin/activate"
else
    echo "Unknown OS: $OS"
    return 1
fi

# Example: Navigate to the project folder automatically
PROJECT_DIR="$BASE_PATH/ScreenArt"

if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
    echo "OS: $OS | Virtual env activated!"
    echo "Project Directory: $PROJECT_DIR"
else
    echo "Error: Could not find venv at $VENV_PATH"
fi
