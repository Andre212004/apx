#!/usr/bin/sh
set -eu

disk=/dev/nvme0n1
partition=/dev/nvme0n1p2
mapping=/dev/mapper/cryptroot
work=/run/apx-native-windows-root
esp=/run/apx-native-windows-esp
status_file="$esp/EFI/APX/recovery/windows-lifecycle-v1.status"
p2_start=2099200
full_p2_sectors=998115983
disk_last_plus_one=1000215183
sectors_per_gib=2097152
luks_overhead_sectors=32768

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
    /usr/bin/printf 'APX WINDOWS LIFECYCLE FAILED: %s\n' "$1" >/dev/console
    record_status "failed:$action:$size_gib:$generation:$1" || true
    reboot_now
}

action=
size_gib=
generation=
for token in $(/usr/bin/cat /proc/cmdline); do
    case "$token" in
        apx.native_windows_action=*) action=${token#*=} ;;
        apx.native_windows_size_gib=*) size_gib=${token#*=} ;;
        apx.native_windows_generation=*) generation=${token#*=} ;;
    esac
done
case "$action" in create|delete) ;; *) action=unknown; fail action ;; esac
case "$size_gib" in 80|120|160) ;; *) fail size ;; esac
case "$generation" in *[!0-9a-f-]*|'') fail generation ;; esac
test "${#generation}" = 36 || fail generation-length
case "$(/usr/bin/cat /proc/cmdline)" in *apx.native_windows_lifecycle=1*) ;; *) fail cmdline ;; esac

tail_start=$(( (disk_last_plus_one - size_gib * sectors_per_gib) / 2048 * 2048 ))
target_p2_sectors=$(( tail_start - p2_start ))
target_p2_bytes=$(( target_p2_sectors * 512 ))
target_btrfs_bytes=$(( (target_p2_sectors - luks_overhead_sectors) * 512 ))
reserved_bytes=$(( (disk_last_plus_one - tail_start) * 512 ))

/usr/bin/printf '\nAPX WINDOWS · %s · %s GiB\n' "$action" "$size_gib" >/dev/console
/usr/bin/mkdir -p "$esp" "$work" || fail mkdir
/usr/bin/mount -t vfat -o rw /dev/nvme0n1p1 "$esp" || fail mount-esp
/usr/bin/mkdir -p "$esp/EFI/APX/recovery" || fail mkdir-recovery
/usr/bin/printf 'running:%s:%s:%s\n' "$action" "$size_gib" "$generation" >"$status_file" || fail status-running
/usr/bin/sync || fail sync-before
/usr/bin/umount "$esp" || fail unmount-esp-before-storage

test "$(/usr/bin/cat /sys/class/power_supply/ADP0/online)" = 1 || fail ac-offline
test "$(/usr/bin/blockdev --getsize64 "$disk")" = 512110190592 || fail disk-size
case "$(/usr/bin/cat /sys/block/nvme0n1/device/serial)" in *S4DYNX0R253702*) ;; *) fail disk-serial ;; esac
test "$(/usr/bin/sfdisk --disk-id "$disk")" = AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 || fail disk-id
test -b "$mapping" || fail cryptroot-missing
test "$(/usr/bin/blkid -s PARTUUID -o value /dev/nvme0n1p1)" = 9625f250-9acc-453a-ae63-0c863ade440f || fail esp-identity
test "$(/usr/bin/blkid -s PARTUUID -o value "$partition")" = 8835c8f0-f02f-4fc2-9035-5dbbc191df9e || fail crypt-identity

if test "$action" = create; then
    test "$(/usr/bin/blockdev --getsz "$partition")" = "$full_p2_sectors" || fail full-partition-size
    for number in 3 4 5 6; do test ! -b "/dev/nvme0n1p$number" || fail unexpected-tail-partition; done
    /usr/bin/mount -t btrfs -o rw,subvolid=5 "$mapping" "$work" || fail mount-btrfs
    /usr/bin/btrfs filesystem resize "1:$target_btrfs_bytes" "$work" || fail shrink-btrfs
    /usr/bin/sync || fail sync-btrfs
    /usr/bin/umount "$work" || fail unmount-btrfs
    /usr/bin/systemctl stop systemd-cryptsetup@cryptroot.service || fail close-cryptroot
    test ! -e "$mapping" || fail cryptroot-still-open
    /usr/bin/sfdisk --wipe never -N 2 "$disk" <<EOF >/dev/console || fail shrink-gpt
start=$p2_start, size=$target_p2_sectors, type=CA7D7CCB-63ED-4C53-861C-1742536059CC, uuid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E, name="APX_CRYPT"
EOF
    /usr/bin/sfdisk --verify "$disk" >/dev/console || fail verify-shrunk-gpt
    test "$(/usr/bin/blockdev --getsize64 "$partition")" = "$target_p2_bytes" || fail kernel-shrunk-size
    record_status "success:create:$size_gib:$generation:$reserved_bytes" || fail status-success-create
else
    test "$(/usr/bin/blockdev --getsz "$partition")" = "$target_p2_sectors" || fail reserved-partition-size
    test "$(/usr/bin/cat /sys/class/block/nvme0n1p3/start)" = "$tail_start" || fail windows-tail-start
    test "$(/usr/bin/blockdev --getsz /dev/nvme0n1p3)" = "$((981340160 - tail_start))" || fail windows-size
    test "$(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p3)" = ebd0a0a2-b9e5-4433-87c0-68b6b72699c7 || fail windows-type
    test "$(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value /dev/nvme0n1p3)" = 099c31d8-313a-4aba-b0e0-2b59502c9674 || fail windows-identity
    test "$(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p3)" = ntfs || fail windows-filesystem
    test "$(/usr/bin/blkid -s LABEL -o value /dev/nvme0n1p3)" = APXWINTARGET || fail windows-label
    test "$(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p4)" = c12a7328-f81f-11d2-ba4b-00a0c93ec93b || fail setup-type
    test "$(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value /dev/nvme0n1p4)" = 309bebb6-5c32-4e21-9c92-6d758e51389d || fail setup-identity
    test "$(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p4)" = vfat || fail setup-filesystem
    test "$(/usr/bin/blkid -s LABEL -o value /dev/nvme0n1p4)" = APXWINSETUP || fail setup-label
    test "$(/usr/bin/cat /sys/class/block/nvme0n1p4/start)" = 981340160 || fail setup-start
    test "$(/usr/bin/blockdev --getsz /dev/nvme0n1p4)" = 18874368 || fail setup-size
    test ! -b /dev/nvme0n1p5 && test ! -b /dev/nvme0n1p6 || fail unexpected-tail-partition
    for number in 3 4; do /usr/bin/blkdiscard -f "/dev/nvme0n1p$number" || fail "discard-p$number"; done
    /usr/bin/sync || fail sync-discard
    /usr/bin/systemctl stop systemd-cryptsetup@cryptroot.service || fail close-cryptroot
    test ! -e "$mapping" || fail cryptroot-still-open
    /usr/bin/sfdisk --delete --no-reread --no-tell-kernel "$disk" 4 3 >/dev/console || fail delete-windows-gpt
    /usr/bin/sfdisk --wipe never -N 2 "$disk" <<EOF >/dev/console || fail grow-gpt
start=$p2_start, size=$full_p2_sectors, type=CA7D7CCB-63ED-4C53-861C-1742536059CC, uuid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E, name="APX_CRYPT"
EOF
    /usr/bin/sfdisk --verify "$disk" >/dev/console || fail verify-grown-gpt
    test "$(/usr/bin/blockdev --getsz "$partition")" = "$full_p2_sectors" || fail kernel-grown-size
    record_status "success:delete:$size_gib:$generation:$reserved_bytes" || fail status-success-delete
fi

/usr/bin/printf 'APX WINDOWS · OPERAÇÃO OFFLINE CONCLUÍDA · A REINICIAR\n' >/dev/console
reboot_now
