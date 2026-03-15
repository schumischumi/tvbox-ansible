#!/usr/bin/env bash

set -euo pipefail

PIDFILE="/tmp/auto-dvd-mpv.pid"

find_dvd_with_media() {
    # Find optical drives
    for dev in $(lsblk -nr -o NAME,TYPE | awk '$2=="rom"{print $1}'); do
        device="/dev/$dev"

        if udevadm info --query=property --name="$device" | grep -q '^ID_CDROM_DVD=1'; then
            echo "$device"
            return 0
        fi
    done

    return 1
}

start_mpv() {
    if [[ -f "$PIDFILE" ]]; then
        pid=$(cat "$PIDFILE")
        if kill -0 "$pid" 2>/dev/null; then
            return
        fi
    fi

    /usr/bin/mpv dvd:// --fullscreen &
    echo $! > "$PIDFILE"
}

stop_mpv() {
    if [[ -f "$PIDFILE" ]]; then
        pid=$(cat "$PIDFILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
        rm -f "$PIDFILE"
    fi
}

main() {
    if find_dvd_with_media >/dev/null; then
        start_mpv
    else
        stop_mpv
    fi
}

main
