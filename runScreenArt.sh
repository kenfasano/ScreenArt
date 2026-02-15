#!/usr/bin/env zsh

# 1. Dynamic Path Detection
SCRIPT_DIR=${0:a:h}            # .../Scripts/ScreenArt
PROJECT_PARENT_DIR=${SCRIPT_DIR:h} # .../Scripts (Where the venvs live!)

echo "📂 Script Location: $SCRIPT_DIR"
echo "📂 Venv Location:   $PROJECT_PARENT_DIR"

# 2. Detect OS and Select Venv Name
OS_TYPE=$(uname)
if [[ "$OS_TYPE" == "Darwin" ]]; then
    VENV_NAME=".venv_mac"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    VENV_NAME=".venv_linux"
else
    echo "❌ Unknown OS: $OS_TYPE"
    exit 1
fi

# 3. Define the Explicit Python Path
# FIX: Look in the Parent Dir (Scripts/) for the venv, NOT inside ScreenArt/
PYTHON_EXEC="$PROJECT_PARENT_DIR/$VENV_NAME/bin/python"

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
exec "$PYTHON_EXEC" -m ScreenArt.runScreenArt
