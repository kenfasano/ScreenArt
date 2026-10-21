# This should show a UserFolderPaths array — adding a folder writes to a nested DSKDesktopPrefPane -> 
# UserFolderPaths array in that plist, which is what makes a folder show up as its own section in 
# System Settings > Wallpaper distinct from "Your Photos." Your ScreenArt output directory is very 
# likely sitting in that array.
defaults read ~/Library/Preferences/com.apple.systempreferences.plist DSKDesktopPrefPane
