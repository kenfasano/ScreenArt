#!/bin/zsh

# Detect Operating System
OS="$(uname)"

if [[ "$OS" == "Darwin" ]]; then
    # macOS path
    DEST_DIR="/Users/kenfasano/Google Drive/My Drive/shared/Scripts/ScreenArt/"
elif [[ "$OS" == "Linux" ]]; then
    # Fedora/Linux path (Adjust this if your mount point differs)
    DEST_DIR="$HOME/Google Drive/shared/Scripts/ScreenArt/"
else
    echo "Unknown OS: $OS"
    exit 1
fi

# 1. Synchronize with Google Drive
# NOTE: The exclude path is relative to the source directory
rsync -rtuv \
    --exclude '_*' \
    --exclude '._*' \
    --exclude '.git' \
    --exclude '.gitignore' \
    --exclude '__pycache__' \
    --exclude 'Images/' \
    ~/Scripts/ScreenArt/ \
    "$DEST_DIR"

# 2. Ask for the commit message
echo -n "Enter commit message: "
read commit_message

# 3. Exit with a complaint if the message is empty
if [[ -z "$commit_message" ]]; then
    echo "❌ Error: You must provide a commit message. Sync aborted."
    exit 1
fi

echo "🚀 Starting sync for ScreenArt..."

# 4. Clear the git cache 
# This ensures that files newly added to .gitignore (like Images/) are actually dropped
git rm -r --cached . > /dev/null 2>&1

# 5. Add all files (respecting the updated .gitignore)
git add .

# 6. Commit with your message
git commit -m "$commit_message"

# 7. Push to the main branch
echo "git pushing to origin main..."
git push origin main

echo "✅ Done!"
