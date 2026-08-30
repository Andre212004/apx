#!/usr/bin/sh
set -eu

disk=/dev/nvme0n1
partition=/dev/nvme0n1p2
mapping=/dev/mapper/cryptroot
work=/run/apx-native-windows-root
esp=/run/apx-native-windows-esp
status_file="$esp/EFI/APX/recovery/windows-storage-maintenance-v1.status"

record_status() {
    status="$1"
    /usr/bin/mkdir -p "$esp" || return 1
    if ! /usr/bin/mountpoint -q "$esp"; then
        /usr/bin/mount -t vfat -o rw /dev/nvme0n1p1 "$esp" || return 1
    fi
    /usr/bin/mkdir -p "$esp/EFI/APX/recovery" || return 1
    /usr/bin/printf '%s\n' "$status" >"$status_file" || return 1
    /usr/bin/sync || return 1
    /usr/bin/umount "$esp" || return 1
}

reboot_now() {
    /usr/bin/sync || true
    /usr/bin/systemctl --no-block --force reboot || true
    while :; do /usr/bin/sleep 1; done
}

fail() {
    /usr/bin/printf 'APX WINDOWS MAINTENANCE FAILED: %s\n' "$1" >/dev/console
    record_status "failed:$1" || true
    reboot_now
}

/usr/bin/printf '\nAPX WINDOWS · RESERVA FÍSICA DE 120 GiB\n' >/dev/console
/usr/bin/mkdir -p "$esp" "$work" || fail mkdir
/usr/bin/mount -t vfat -o rw /dev/nvme0n1p1 "$esp" || fail mount-esp
/usr/bin/mkdir -p "$esp/EFI/APX/recovery" || fail mkdir-recovery
/usr/bin/printf 'running\n' >"$status_file" || fail status-running
/usr/bin/sync || fail sync-before
/usr/bin/umount "$esp" || fail unmount-esp-before-storage

case "$(/usr/bin/cat /proc/cmdline)" in
    *apx.native_windows_reserve=1*) ;;
    *) fail cmdline ;;
esac
test "$(/usr/bin/cat /sys/class/power_supply/ADP0/online)" = 1 || fail ac-offline
test "$(/usr/bin/blockdev --getsize64 "$disk")" = 512110190592 || fail disk-size
case "$(/usr/bin/cat /sys/block/nvme0n1/device/serial)" in
    *S4DYNX0R253702*) ;;
    *) fail disk-serial ;;
esac
test "$(/usr/bin/blockdev --getsize64 "$partition")" = 511035383296 || fail partition-size
test -b "$mapping" || fail cryptroot-missing

/usr/bin/mount -t btrfs -o rw,subvolid=5 "$mapping" "$work" || fail mount-btrfs
/usr/bin/btrfs filesystem resize 1:382169251840 "$work" || fail shrink-btrfs
/usr/bin/sync || fail sync-btrfs
/usr/bin/umount "$work" || fail unmount-btrfs
/usr/bin/systemctl stop systemd-cryptsetup@cryptroot.service || fail close-cryptroot
test ! -e "$mapping" || fail cryptroot-still-open

/usr/bin/sfdisk --wipe never -N 2 "$disk" <<'EOF' >/dev/console || fail shrink-gpt
start=2099200, size=746457088, type=CA7D7CCB-63ED-4C53-861C-1742536059CC, uuid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E, name="APX_CRYPT"
EOF
/usr/bin/sfdisk --verify "$disk" >/dev/console || fail verify-gpt
test "$(/usr/bin/blockdev --getsize64 "$partition")" = 382186029056 || fail kernel-partition-size
record_status 'success:128849354240' || fail status-success
/usr/bin/printf 'APX WINDOWS · 120 GiB RESERVADOS · A REINICIAR\n' >/dev/console
reboot_now
