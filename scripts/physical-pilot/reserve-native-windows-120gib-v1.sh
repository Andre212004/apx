#!/usr/bin/bash
set -euo pipefail

# One exact online filesystem/GPT shrink for the APX pilot disk. The active
# dm-crypt mapping deliberately keeps its old kernel-visible bound until the
# mandatory reboot; on the next boot it adopts the smaller p2 automatically.
# The resulting tail is left unallocated for Windows Setup.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly partition=/dev/nvme0n1p2
readonly mapping=cryptroot
readonly backup=/var/lib/apx/backups/20260825-native-windows-storage-v2
readonly esp_recovery=/boot/EFI/APX/recovery
readonly storage_source="$repository/config/native-environments/windows-storage-v1.json"
readonly storage_target=/var/lib/apx/native-environments/windows-storage-v1.json
readonly new_partition_sectors=746457088
readonly new_filesystem_bytes=382169251840
stage=0

fail() { /usr/bin/printf 'APX Windows storage reservation refused: %s\n' "$1" >&2; exit 2; }

# Retained only as evidence of the rejected online experiment. The physical
# reservation is now performed exclusively by the signed one-shot initramfs,
# where Btrfs is unmounted and dm-crypt is closed before the GPT write.
fail "online method retired; use APX Windows Storage Maintenance"

[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail "physical-pilot marker differs"
[[ $PWD == "$repository" ]] || fail "run from the dedicated repository"
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail "connect the AC adapter first"
[[ $(< /sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery charge is below 40%"
[[ $(/usr/bin/blockdev --getsize64 "$disk") == 512110190592 ]] || fail "disk size differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/blockdev --getsize64 "$partition") == 511035383296 ]] || fail "encrypted partition is not at the original size"
[[ $(/usr/bin/cryptsetup status "$mapping" | /usr/bin/awk '$1 == "size:" {print $2}') == 998083215 ]] || fail "dm-crypt size differs"
[[ $(/usr/bin/findmnt -n -o SOURCE / | /usr/bin/sed 's/\[.*//') == /dev/mapper/cryptroot ]] || fail "root mapping differs"
[[ $(/usr/bin/findmnt -n -o FSTYPE /) == btrfs ]] || fail "root filesystem differs"
[[ $(/usr/bin/machinectl list --no-legend | /usr/bin/awk '{print $1}') == apx-hub ]] || fail "the Hub is not the only active machine"
[[ ! -e /run/apx/environment-handoff-v1.lock && ! -e /run/apx/environment-management-v1.lock ]] || fail "an Environment operation is active"
[[ ! -e $backup && ! -e $storage_target ]] || fail "the reservation already exists"
[[ -f $storage_source && ! -L $storage_source ]] || fail "storage marker source differs"
/usr/bin/btrfs scrub status / | /usr/bin/grep -Fq 'Status:           finished' || fail "Btrfs scrub is not complete"
/usr/bin/btrfs scrub status / | /usr/bin/grep -Fq 'Error summary:    no errors found' || fail "Btrfs scrub found errors"
/usr/bin/python3 - "$disk" <<'PY' || fail "current GPT layout differs"
import json, subprocess, sys
value=json.loads(subprocess.run(("/usr/bin/sfdisk","--json",sys.argv[1]),check=True,text=True,capture_output=True).stdout)
table=value["partitiontable"]
parts=table["partitions"]
assert table["id"] == "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275"
assert len(parts) == 2
assert (parts[1]["node"], parts[1]["start"], parts[1]["size"], parts[1]["uuid"], parts[1]["name"]) == (
    "/dev/nvme0n1p2", 2099200, 998115983, "8835C8F0-F02F-4FC2-9035-5DBBC191DF9E", "APX_CRYPT")
PY

/usr/bin/sfdisk --no-act --no-reread --no-tell-kernel --wipe never -N 2 "$disk" <<'EOF' >/dev/null
start=2099200, size=746457088, type=CA7D7CCB-63ED-4C53-861C-1742536059CC, uuid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E, name="APX_CRYPT"
EOF

/usr/bin/install -d -m 0700 -o root -g root -- "$backup"
/usr/bin/install -d -m 0700 -o root -g root -- "$esp_recovery"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/sfdisk --backup-pt-sectors -O "$backup/gpt" "$disk" >/dev/null
/usr/bin/cryptsetup luksHeaderBackup "$partition" --header-backup-file "$backup/apx-crypt-before-windows-v2.luks2"
/usr/bin/install -m 0600 -o root -g root -- "$backup/apx-crypt-before-windows-v2.luks2" "$esp_recovery/apx-crypt-before-windows-v2.luks2"
/usr/bin/sync

rollback() {
    trap - ERR
    /usr/bin/printf 'APX reservation failed at stage %s; restoring the original bounds...\n' "$stage" >&2
    if (( stage >= 2 )); then
        /usr/bin/sfdisk --no-reread --no-tell-kernel --wipe never "$disk" <"$backup/gpt-before.sfdisk" || true
    fi
    if (( stage >= 1 )); then
        /usr/bin/btrfs filesystem resize 1:max / || true
    fi
    /usr/bin/sync
    fail "the original online sizes were requested again; inspect the backup before retrying"
}
trap rollback ERR

[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || false
/usr/bin/btrfs filesystem resize "1:$new_filesystem_bytes" /
stage=1
/usr/bin/btrfs filesystem usage -b / | /usr/bin/grep -Fq '382169251840' \
    || { /usr/bin/btrfs filesystem show / | /usr/bin/grep -Fq '355.92GiB'; }

[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || false
/usr/bin/sfdisk --no-reread --no-tell-kernel --wipe never -N 2 "$disk" <<'EOF' >/dev/null
start=2099200, size=746457088, type=CA7D7CCB-63ED-4C53-861C-1742536059CC, uuid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E, name="APX_CRYPT"
EOF
stage=2
/usr/bin/python3 - "$disk" <<'PY'
import json, subprocess, sys
value=json.loads(subprocess.run(("/usr/bin/sfdisk","--json",sys.argv[1]),check=True,text=True,capture_output=True).stdout)
parts=value["partitiontable"]["partitions"]
assert (parts[1]["start"], parts[1]["size"], parts[1]["uuid"]) == (
    2099200, 746457088, "8835C8F0-F02F-4FC2-9035-5DBBC191DF9E")
PY
/usr/bin/sfdisk --verify "$disk"
[[ $(/usr/bin/blockdev --getsize64 "$partition") == 511035383296 ]]
[[ $(/usr/bin/cryptsetup status "$mapping" | /usr/bin/awk '$1 == "size:" {print $2}') == 998083215 ]]
/usr/bin/install -m 0400 -o root -g root -- "$storage_source" "$storage_target"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-after.sfdisk"
/usr/bin/sync
trap - ERR
/usr/bin/printf 'Reserved 128849354240 bytes (120.0003 GiB) for native Windows in the on-disk GPT; reboot APX now so dm-crypt adopts the new p2 bound.\n'
