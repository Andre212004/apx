#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly STATE=/var/lib/apx
readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly RUNTIME_SOURCE=$SCRIPT_DIR/../virtual-lab/apx-lab-runtime.py
readonly RUNTIME_TARGET=/usr/lib/apx/apx-lab-runtime.py
readonly RUNTIME_SHA256=a05c6a032f8ff1f0bb77f10635b4b1b1b47d7ce68bdfb4d0c7689ad9bb042e36
readonly NAME=development
readonly ENVIRONMENT=$STATE/environments/$NAME
readonly REGISTRATION=$ENVIRONMENT/registration.json
readonly OLD_ROOT_BYTES=4294967296
readonly OLD_HOME_BYTES=2147483648
readonly NEW_ROOT_LIMIT=16G
readonly NEW_HOME_LIMIT=8G
readonly NEW_ROOT_BYTES=17179869184
readonly NEW_HOME_BYTES=8589934592
readonly APPROVAL='RESIZE development FROM 4G+2G TO 16G+8G'
TOP_LEVEL=

fail() {
  printf 'APX Development quota recovery refused: %s\n' "$*" >&2
  exit 1
}

validate_quota_status() {
  python -c '
import sys

fields = {}
for raw_line in sys.stdin:
    if ":" not in raw_line:
        continue
    key, value = raw_line.split(":", 1)
    key = " ".join(key.strip().lower().split())
    value = " ".join(value.strip().lower().split())
    if key in {"enabled", "status", "mode", "inconsistent", "override limits", "rescan status"}:
        if key in fields:
            raise SystemExit(1)
        fields[key] = value

enabled_values = [fields[key] for key in ("enabled", "status") if key in fields]
if len(enabled_values) != 1 or enabled_values[0] not in {"yes", "enabled"}:
    raise SystemExit(1)
if fields.get("mode") not in {"qgroup", "qgroup (full accounting)"}:
    raise SystemExit(1)
if fields.get("inconsistent") != "no":
    raise SystemExit(1)
if fields.get("override limits") == "yes" or fields.get("rescan status") == "running":
    raise SystemExit(1)
'
}

if [[ ${1-} == --validate-quota-status ]]; then
  [[ $# == 1 ]] || exit 2
  validate_quota_status
  exit
fi
[[ $# == 0 ]] || fail 'arguments are not accepted'

cleanup_top_level() {
  if [[ -n $TOP_LEVEL ]]; then
    if mountpoint -q "$TOP_LEVEL"; then
      umount "$TOP_LEVEL"
    fi
    rmdir "$TOP_LEVEL"
  fi
}

[[ $(id -u) == 0 ]] || fail 'host root is required'
[[ $(systemd-detect-virt) == none ]] || fail 'physical-machine pilot required'
[[ $(< /etc/hostname) == apx-host ]] || fail 'wrong host identity'
[[ -f /etc/apx-physical-pilot ]] || fail 'reviewed physical foundation marker absent'
grep -qx 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
  || fail 'wrong physical-pilot profile'
[[ $(< /sys/class/dmi/id/sys_vendor) == LENOVO ]] || fail 'wrong system vendor'
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'wrong product identity'
[[ $(< /sys/class/dmi/id/board_name) == LNVNB161216 ]] || fail 'wrong board identity'
[[ $(findmnt -n -o FSTYPE "$STATE") == btrfs ]] || fail 'APX state is not Btrfs'
filesystem_uuid=$(findmnt -n -o UUID -T "$STATE")
[[ $filesystem_uuid =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]] \
  || fail 'APX Btrfs filesystem UUID is unavailable or malformed'
[[ $(findmnt -rn -t btrfs -o UUID | awk -v wanted="$filesystem_uuid" '$1 == wanted { count++ } END { print count+0 }') -ge 1 ]] \
  || fail 'APX Btrfs filesystem identity is not mounted'
TOP_LEVEL=/run/apx-quota-recovery-v3
[[ ! -e $TOP_LEVEL ]] || fail 'private top-level recovery mount path already exists'
install -d -m0700 "$TOP_LEVEL"
trap cleanup_top_level EXIT
mount -t btrfs -o subvolid=5 "UUID=$filesystem_uuid" "$TOP_LEVEL" \
  || fail 'could not create the private Btrfs top-level recovery mount'
[[ $(findmnt -n -o FSTYPE -T "$TOP_LEVEL") == btrfs ]] \
  || fail 'private recovery mount is not Btrfs'
[[ $(findmnt -n -o UUID -T "$TOP_LEVEL") == "$filesystem_uuid" ]] \
  || fail 'private recovery mount has the wrong filesystem identity'
[[ $(btrfs inspect-internal rootid "$TOP_LEVEL") == 5 ]] \
  || fail 'private recovery mount is not Btrfs subvolume ID 5'
[[ -f $RUNTIME_SOURCE && ! -L $RUNTIME_SOURCE ]] || fail 'reviewed runtime source is absent or unsafe'
[[ $(sha256sum "$RUNTIME_SOURCE" | awk '{print $1}') == "$RUNTIME_SHA256" ]] \
  || fail 'runtime source identity does not match this recovery release'
[[ -f $REGISTRATION && ! -L $REGISTRATION ]] || fail 'Development registration is absent or unsafe'

readarray -t registration < <(python - "$REGISTRATION" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    value = json.load(stream)
required = {"name": "development", "role": "development", "state": "stopped"}
if any(value.get(key) != expected for key, expected in required.items()):
    raise SystemExit(1)
print(value.get("generation", ""))
print(value.get("release", ""))
PY
) || fail 'Development is not the stopped registered Development Environment'
[[ ${#registration[@]} == 2 && -n ${registration[0]} && -n ${registration[1]} ]] \
  || fail 'Development registration identity is incomplete'

machine_state=$(machinectl show apx-development --property=State --value 2>/dev/null || true)
[[ -z $machine_state ]] || fail 'Development runtime is still registered'
for label in root home; do
  path=$ENVIRONMENT/$label
  [[ -d $path && ! -L $path ]] || fail "$label path is absent or unsafe"
  btrfs subvolume show "$path" >/dev/null || fail "$label is not a Btrfs subvolume"
done

quota_status=$(btrfs quota status "$TOP_LEVEL") || fail 'quota status is unavailable'
validate_quota_status <<<"$quota_status" \
  || fail 'quota accounting is disabled, non-qgroup, inconsistent, overridden, rescanning, or malformed'

root_id=$(btrfs inspect-internal rootid "$ENVIRONMENT/root")
home_id=$(btrfs inspect-internal rootid "$ENVIRONMENT/home")
[[ $root_id =~ ^[0-9]+$ && $home_id =~ ^[0-9]+$ && $root_id != "$home_id" ]] \
  || fail 'could not resolve distinct Development qgroups'

qgroups=$(btrfs qgroup show --raw -reF "$TOP_LEVEL") || fail 'qgroup limits are unavailable'
limit_for() {
  local identity=$1
  awk -v wanted="0/$identity" '$1 == wanted { print $(NF-1), $NF; found=1 } END { if (!found) exit 1 }' \
    <<<"$qgroups"
}
read -r root_referenced root_exclusive < <(limit_for "$root_id") \
  || fail 'Development root qgroup is absent'
read -r home_referenced home_exclusive < <(limit_for "$home_id") \
  || fail 'Development home qgroup is absent'
[[ $root_referenced == "$OLD_ROOT_BYTES" && $root_exclusive == "$OLD_ROOT_BYTES" ]] \
  || fail 'Development root does not have the expected old 4G limits'
[[ $home_referenced == "$OLD_HOME_BYTES" && $home_exclusive == "$OLD_HOME_BYTES" ]] \
  || fail 'Development home does not have the expected old 2G limits'

printf 'Development generation: %s\nRelease: %s\nRoot qgroup: 0/%s (4G -> 16G)\nHome qgroup: 0/%s (2G -> 8G)\n' \
  "${registration[0]}" "${registration[1]}" "$root_id" "$home_id"
read -r -p "Type ${APPROVAL}: " entered
[[ $entered == "$APPROVAL" ]] || fail 'exact approval was not entered'

rollback() {
  btrfs qgroup limit "$OLD_ROOT_BYTES" "0/$root_id" "$TOP_LEVEL" || true
  btrfs qgroup limit -e "$OLD_ROOT_BYTES" "0/$root_id" "$TOP_LEVEL" || true
  btrfs qgroup limit "$OLD_HOME_BYTES" "0/$home_id" "$TOP_LEVEL" || true
  btrfs qgroup limit -e "$OLD_HOME_BYTES" "0/$home_id" "$TOP_LEVEL" || true
}
trap rollback ERR
btrfs qgroup limit "$NEW_ROOT_LIMIT" "0/$root_id" "$TOP_LEVEL"
btrfs qgroup limit -e "$NEW_ROOT_LIMIT" "0/$root_id" "$TOP_LEVEL"
btrfs qgroup limit "$NEW_HOME_LIMIT" "0/$home_id" "$TOP_LEVEL"
btrfs qgroup limit -e "$NEW_HOME_LIMIT" "0/$home_id" "$TOP_LEVEL"

qgroups=$(btrfs qgroup show --raw -reF "$TOP_LEVEL")
read -r root_referenced root_exclusive < <(limit_for "$root_id")
read -r home_referenced home_exclusive < <(limit_for "$home_id")
[[ $root_referenced == "$NEW_ROOT_BYTES" && $root_exclusive == "$NEW_ROOT_BYTES" ]]
[[ $home_referenced == "$NEW_HOME_BYTES" && $home_exclusive == "$NEW_HOME_BYTES" ]]
install -Dm0755 "$RUNTIME_SOURCE" "$RUNTIME_TARGET"
[[ $(sha256sum "$RUNTIME_TARGET" | awk '{print $1}') == "$RUNTIME_SHA256" ]]
trap - ERR

printf 'APX_DEVELOPMENT_QUOTA_RECOVERY_COMPLETE generation=%s root_qgroup=0/%s home_qgroup=0/%s\n' \
  "${registration[0]}" "$root_id" "$home_id"
