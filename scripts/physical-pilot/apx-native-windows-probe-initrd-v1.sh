#!/usr/bin/sh
set -eu

esp=/run/apx-native-windows-probe-esp
status_file="$esp/EFI/APX/recovery/windows-storage-probe-v1.status"

/usr/bin/printf 'APX WINDOWS: maintenance UKI loaded; recording pre-unlock probe\n' >/dev/console
/usr/bin/mkdir -p "$esp"
/usr/bin/mount -t vfat -o rw /dev/nvme0n1p1 "$esp"
/usr/bin/mkdir -p "$esp/EFI/APX/recovery"
{
    /usr/bin/printf 'stage=uki-loaded-before-unlock\n'
    /usr/bin/printf 'cmdline='
    /usr/bin/cat /proc/cmdline
} >"$status_file"
/usr/bin/sync
/usr/bin/umount "$esp"
/usr/bin/printf 'APX WINDOWS: pre-unlock probe recorded\n' >/dev/console
