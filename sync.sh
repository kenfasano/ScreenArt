#!/bin/zsh

# 1. Synchronize with Google Drive
rsync -rtuv \
	--exclude '_*' \
	--exclude '._*' \
	--exclude '.git' \
	--exclude '__pycache__' \
	~/Scripts/ScreenArt/ \
   "/home/kenfasano/Google Drive/shared/Scripts/ScreenArt/"

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
# This ensures that files newly added to .gitignore (like .jpg) are actually dropped
git rm -r --cached . > /dev/null 2>&1

# 5. Add all files (respecting the updated .gitignore)
git add .

# 6. Commit with your message
git commit -m "$commit_message"

# 7. Push to the main branch
echo "git pushing to origin main..."
git push origin main

echo "✅ Done!"

