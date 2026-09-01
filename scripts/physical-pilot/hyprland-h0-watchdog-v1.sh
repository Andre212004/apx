#!/usr/bin/env bash
set -euo pipefail

readonly ACTION=${1:-}
readonly NAME=codex-test-hyprland-h0-v1
readonly GENERATION=c4fc5c49-4106-4a56-b1f0-13bffa41a0c1
readonly UNIT=apx-h0-graphical-c4fc5c49.service
readonly MACHINE=apx-codex-test-hyprland-h0-v1
readonly ENVIRONMENT=/var/lib/apx/environments/codex-test-hyprland-h0-v1
readonly REGISTRATION=$ENVIRONMENT/registration.json

[[ $ACTION == --expire ]]
[[ $(id -u) == 0 ]]
[[ -f $REGISTRATION && ! -L $REGISTRATION ]]

python - "$REGISTRATION" "$NAME" "$GENERATION" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
value = json.loads(path.read_text())
if value.get("name") != sys.argv[2] or value.get("generation") != sys.argv[3]:
    raise SystemExit("H0 watchdog registration identity changed")
if value.get("role") != "graphical-h0" or value.get("release") != "hyprland-h0-v1":
    raise SystemExit("H0 watchdog role or release changed")
PY

# Stopping this one transient unit revokes its complete DevicePolicy grant.
systemctl stop "$UNIT" 2>/dev/null || true
/usr/bin/chvt 1

for _ in {1..100}; do
  machine_state=$(machinectl show "$MACHINE" --property=State --value 2>/dev/null || true)
  unit_state=$(systemctl is-active "$UNIT" 2>/dev/null || true)
  mount_count=$(awk -v path="$ENVIRONMENT" 'index($0,path){count++} END{print count+0}' /proc/self/mountinfo)
  process_count=$(python - "$MACHINE" <<'PY'
import pathlib, sys
needle = ("--machine=" + sys.argv[1]).encode()
count = 0
for item in pathlib.Path('/proc').iterdir():
    if not item.name.isdigit():
        continue
    try:
        data = (item / 'cmdline').read_bytes()
    except OSError:
        continue
    count += needle in data.split(b'\0')
print(count)
PY
)
  if [[ -z $machine_state && $unit_state != active && $unit_state != activating && $mount_count == 0 && $process_count == 0 ]]; then
    printf 'h0-watchdog: tty1-restored zero-residue\n'
    exit 0
  fi
  read -r -t 0.1 _ </dev/null || true
done

printf 'h0-watchdog: residue-remains; preserve failed unit and inspect from tty1\n' >&2
exit 1
