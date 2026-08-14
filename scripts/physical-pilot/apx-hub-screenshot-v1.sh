#!/usr/bin/env bash
set -euo pipefail

readonly screenshot_directory=/home/apx/Pictures/Screenshots
mkdir -p "$screenshot_directory"
readonly screenshot_path="$screenshot_directory/APX-$(date +%Y%m%d-%H%M%S).png"
/usr/bin/grim "$screenshot_path"
