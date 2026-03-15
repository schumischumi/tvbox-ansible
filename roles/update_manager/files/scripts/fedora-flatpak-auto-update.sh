#!/bin/bash
# Automatic Fedora + Flatpak updates with conditional reboot
# Triggered by cron at 8 AM

LOG="/var/log/fedora-flatpak-auto-update.log"

echo "=== $(date) ==="

# 1. Check if ANY updates are available
HAS_UPDATES=0

# DNF / Fedora packages (dnf check-update returns 100 = updates available)
dnf check-update --refresh 2>/dev/null
if [ $? -eq 100 ]; then
    HAS_UPDATES=1
    echo "→ DNF updates available"
fi

# Flatpak (remote-ls --updates returns output only if updates exist)
FLATPAK_UPDATES=$(sudo flatpak remote-ls --updates 2>/dev/null)
if [ -n "$FLATPAK_UPDATES" ]; then
    HAS_UPDATES=1
    echo "→ Flatpak updates available"
fi

if [ $HAS_UPDATES -eq 1 ]; then
    echo "→ Applying updates..."

    # Use dnf for Fedora system updates (exactly as you requested)
    sudo dnf upgrade --refresh --assumeyes

    # Flatpak updates (non-interactive, works in cron)
    sudo flatpak update --assumeyes --noninteractive

    echo "→ Updates installed. Rebooting in 1 minute..."

    # Reboot with warning (you can cancel with "sudo shutdown -c" if needed)
    echo "→ Automatic updates installed (Fedora + Flatpak). Rebooting in 1 minute."
    sleep 60
    reboot
else
    echo "→ No updates available. Skipping."
fi
