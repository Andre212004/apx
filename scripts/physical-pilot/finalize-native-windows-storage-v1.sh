#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly partition=/dev/nvme0n1p2
readonly marker_source="$repository/config/native-environments/windows-storage-v1.json"
readonly marker_target=/var/lib/apx/native-environments/windows-storage-v1.json
readonly success_marker=/boot/EFI/APX/recovery/windows-storage-maintenance-v1.status

fail() { /usr/bin/printf 'APX Windows storage finalization refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(< "$success_marker") == success:128849354240 ]] || fail "offline success marker differs"
[[ -f $marker_source && ! -L $marker_source ]] || fail "source marker differs"
[[ $(/usr/bin/blockdev --getsize64 "$partition") == 382186029056 ]] || fail "partition size differs"
[[ $(/usr/bin/cryptsetup status cryptroot | /usr/bin/awk '$1 == "size:" {print $2}') == 746424320 ]] || fail "dm-crypt size differs"
[[ $(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "size:" {print $3; exit}') == 382169251840 ]] || fail "Btrfs size differs"
[[ $(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "slack:" {print $3; exit}') == 0 ]] || fail "Btrfs slack differs"
/usr/bin/python3 - "$disk" <<'PY' || fail "final GPT layout differs"
import json
import subprocess
import sys

table = json.loads(subprocess.run(
    ("/usr/bin/sfdisk", "--json", sys.argv[1]), check=True, text=True, capture_output=True,
).stdout)["partitiontable"]
parts = table["partitions"]
assert table["id"] == "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275"
assert len(parts) == 2
assert (parts[1]["node"], parts[1]["start"], parts[1]["size"], parts[1]["uuid"], parts[1]["name"]) == (
    "/dev/nvme0n1p2", 2099200, 746457088, "8835C8F0-F02F-4FC2-9035-5DBBC191DF9E", "APX_CRYPT",
)
assert table["lastlba"] - (parts[1]["start"] + parts[1]["size"]) + 1 == 251658895
PY
for counter in write_io_errs read_io_errs flush_io_errs generation_errs; do
    [[ $(/usr/bin/btrfs device stats / | /usr/bin/awk -v key=".$counter" '$1 ~ key "$" {print $2}') == 0 ]] \
        || fail "Btrfs $counter is non-zero"
done
if [[ -e $marker_target ]]; then
    [[ -f $marker_target && ! -L $marker_target ]] || fail "installed marker type differs"
    /usr/bin/cmp -s -- "$marker_source" "$marker_target" || fail "installed marker content differs"
else
    /usr/bin/install -m 0400 -o root -g root -- "$marker_source" "$marker_target"
fi
[[ $(/usr/bin/stat -c '%U:%G:%a' "$marker_target") == root:root:400 ]] || fail "installed marker ownership differs"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
/usr/bin/sync
/usr/bin/printf 'APX native Windows storage finalized: 128849354240 bytes reserved.\n'
