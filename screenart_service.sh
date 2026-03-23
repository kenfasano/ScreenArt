#!/bin/zsh
# screenart_service.sh — start, stop, or check status of the ScreenArt LaunchAgent

LABEL="com.kenfasano.screenart"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

usage() {
    echo "Usage: $0 {start|stop|status}"
    exit 1
}

check_plist() {
    if [[ ! -f "$PLIST" ]]; then
        echo "Error: plist not found at $PLIST"
        echo "Install it first with:"
        echo "  cp com.kenfasano.screenart.plist ~/Library/LaunchAgents/"
        exit 1
    fi
}

case "$1" in
    start)
        check_plist
        if launchctl list | grep -q "$LABEL"; then
            echo "ScreenArt is already loaded. Use 'stop' first if you want to restart."
        else
            launchctl load "$PLIST"
            echo "ScreenArt started."
        fi
        ;;

    stop)
        if launchctl list | grep -q "$LABEL"; then
            launchctl unload "$PLIST"
            echo "ScreenArt stopped."
        else
            echo "ScreenArt is not currently running."
        fi
        ;;

    status)
        if launchctl list | grep -q "$LABEL"; then
            PID=$(launchctl list | awk -F'\t' "/$LABEL/ {print \$1}")
            if [[ "$PID" == "-" || -z "$PID" ]]; then
                echo "ScreenArt is loaded but not currently running (may have exited or be waiting)."
            else
                echo "ScreenArt is running. PID: $PID"
            fi
        else
            echo "ScreenArt is not loaded."
        fi
        ;;

    *)
        usage
        ;;
esac
