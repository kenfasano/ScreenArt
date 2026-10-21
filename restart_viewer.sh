launchctl bootout gui/$(id -u)/com.kenfasano.screenart-viewer
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kenfasano.screenart-viewer.plist
launchctl list | grep screenart
