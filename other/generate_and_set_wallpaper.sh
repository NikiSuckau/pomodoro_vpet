#!/usr/bin/env bash
# Generate animated wallpaper video and set as wallpaper using Hidamari

set -e
cd "$(dirname "$0")"

# 1. Generate animation video
python3 live_wallpaper.py

# 2. Launch Hidamari (if not running) or restart it to reload wallpaper
# The user may need to select the output_wallpaper.mp4 in the GUI the first time.
# After that, overwriting the same file will auto-update the wallpaper.

flatpak run io.github.jeffshee.Hidamari &

echo "Wallpaper generated and Hidamari launched. If you haven't already, select 'output_wallpaper.mp4' as your wallpaper in Hidamari."

