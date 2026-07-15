#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

readonly STATE=/var/lib/apx
readonly SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly RUNTIME_SOURCE=$SCRIPT_DIR/../virtual-lab/apx-lab-runtime.py
readonly RUNTIME_TARGET=/usr/lib/apx/apx-lab-runtime.py
readonly RUNTIME_SHA256=5151b89ed53561c1e1f12b05b0b0c50dee483caa8e47f4c2ee397d767ded2b17
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

fail() {
  printf 'APX Development quota recovery refused: %s\n' "$*" >&2
  exit 1
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

quota_status=$(btrfs quota status "$STATE") || fail 'quota status is unavailable'
grep -Eq '^Status:.*enabled|^Enabled:.*yes' <<<"$quota_status" \
  || fail 'quota accounting is disabled'
grep -Eq '^Mode:.*qgroup|^Simple quotas:.*no' <<<"$quota_status" \
  || fail 'traditional qgroup mode is not confirmed'
grep -Eq '^Inconsistent:.*no' <<<"$quota_status" \
  || fail 'quota accounting is inconsistent'
if grep -Eq '^Override limits:.*yes|^Rescan status:.*running' <<<"$quota_status"; then
  fail 'quota limits are overridden or a rescan is running'
fi

root_id=$(btrfs inspect-internal rootid "$ENVIRONMENT/root")
home_id=$(btrfs inspect-internal rootid "$ENVIRONMENT/home")
[[ $root_id =~ ^[0-9]+$ && $home_id =~ ^[0-9]+$ && $root_id != "$home_id" ]] \
  || fail 'could not resolve distinct Development qgroups'

qgroups=$(btrfs qgroup show --raw -reF "$STATE") || fail 'qgroup limits are unavailable'
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
  btrfs qgroup limit "$OLD_ROOT_BYTES" "0/$root_id" "$STATE" || true
  btrfs qgroup limit -e "$OLD_ROOT_BYTES" "0/$root_id" "$STATE" || true
  btrfs qgroup limit "$OLD_HOME_BYTES" "0/$home_id" "$STATE" || true
  btrfs qgroup limit -e "$OLD_HOME_BYTES" "0/$home_id" "$STATE" || true
}
trap rollback ERR
btrfs qgroup limit "$NEW_ROOT_LIMIT" "0/$root_id" "$STATE"
btrfs qgroup limit -e "$NEW_ROOT_LIMIT" "0/$root_id" "$STATE"
btrfs qgroup limit "$NEW_HOME_LIMIT" "0/$home_id" "$STATE"
btrfs qgroup limit -e "$NEW_HOME_LIMIT" "0/$home_id" "$STATE"

qgroups=$(btrfs qgroup show --raw -reF "$STATE")
read -r root_referenced root_exclusive < <(limit_for "$root_id")
read -r home_referenced home_exclusive < <(limit_for "$home_id")
[[ $root_referenced == "$NEW_ROOT_BYTES" && $root_exclusive == "$NEW_ROOT_BYTES" ]]
[[ $home_referenced == "$NEW_HOME_BYTES" && $home_exclusive == "$NEW_HOME_BYTES" ]]
install -Dm0755 "$RUNTIME_SOURCE" "$RUNTIME_TARGET"
[[ $(sha256sum "$RUNTIME_TARGET" | awk '{print $1}') == "$RUNTIME_SHA256" ]]
trap - ERR

printf 'APX_DEVELOPMENT_QUOTA_RECOVERY_COMPLETE generation=%s root_qgroup=0/%s home_qgroup=0/%s\n' \
  "${registration[0]}" "$root_id" "$home_id"
