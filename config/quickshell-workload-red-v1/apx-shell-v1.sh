#!/usr/bin/bash
set -u

readonly config=/home/apx/.config/quickshell/apx/shell.qml
readonly state_dir=/home/apx/.local/state/apx-shell-red-v1
install -d -m 0700 "$state_dir"
exec /usr/bin/quickshell --no-duplicate --path "$config" --no-color --log-times -v \
  >>"$state_dir/quickshell.log" 2>&1
