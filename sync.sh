#!/bin/zsh

# 1. Ask for the commit message
echo -n "Enter commit message: "
read commit_message

# 2. Exit with a complaint if the message is empty
if [[ -z "$commit_message" ]]; then
    echo "❌ Error: You must provide a commit message. Sync aborted."
    exit 1
fi

echo "🚀 Starting sync for ScreenArt..."

# 3. Clear the git cache 
# This ensures that files newly added to .gitignore (like .jpg) are actually dropped
git rm -r --cached . > /dev/null 2>&1

# 4. Add all files (respecting the updated .gitignore)
git add .

# 5. Commit with your message
git commit -m "$commit_message"

# 6. Push to the main branch
echo "git pushing to origin main..."
git push origin main

echo "✅ Done! Your p10k prompt should be clean now."

